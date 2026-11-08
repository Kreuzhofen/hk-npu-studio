"""
Export and validation specification for SD1.5 VAE Encoder.
Exports AutoencoderKL encoder + quant_conv to ONNX (Opset 17) with deterministic
mode, 0.18215 scaling, and NHWC output [1, 64, 64, 4] for Qualcomm QNN compatibility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import torch
from diffusers import AutoencoderKL

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn"
DEFAULT_TARGET_ONNX = DEFAULT_MODEL_DIR / "vae_encoder.onnx"
DEFAULT_VALIDATION_DIR = REPO_ROOT / "temp" / "sd15_vae_validation"

# Local cache candidates for SD1.5 VAE weights
LOCAL_CACHE_CANDIDATES = [
    Path.home() / ".cache" / "huggingface" / "hub" / "models--stable-diffusion-v1-5--stable-diffusion-v1-5" / "snapshots" / "451f4fe16113bff5a5d2269ed5ad43b0592e9a14" / "vae",
    Path.home() / ".cache" / "huggingface" / "hub" / "models--runwayml--stable-diffusion-v1-5" / "snapshots" / "451f4fe16113bff5a5d2269ed5ad43b0592e9a14" / "vae",
]

INPUT_SHAPE = (1, 3, 512, 512)
OUTPUT_SHAPE = (1, 64, 64, 4)
SCALING_FACTOR = 0.18215
OPSET_VERSION = 17


def sha256_file(path: str | Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


class SD15VAEEncoderExportWrapper(torch.nn.Module):
    """
    Deterministic export wrapper for Stable Diffusion 1.5 VAE Encoder.
    Cascades encoder -> quant_conv -> deterministic mean (mode) -> scaling (0.18215) -> NHWC.
    """

    def __init__(self, vae: AutoencoderKL, scaling_factor: float = SCALING_FACTOR) -> None:
        super().__init__()
        self.encoder = vae.encoder
        self.quant_conv = vae.quant_conv
        self.scaling_factor = float(scaling_factor)

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        # image: [1, 3, 512, 512], RGB, normalized to [-1.0, 1.0]
        h = self.encoder(image)
        moments = self.quant_conv(h)
        # Deterministic posterior mean (first 4 channels of 8)
        mean, _ = torch.chunk(moments, 2, dim=1)
        # Apply latent scale factor
        scaled_latent = mean * self.scaling_factor
        # Permute NCHW [1, 4, 64, 64] -> NHWC [1, 64, 64, 4]
        return scaled_latent.permute(0, 2, 3, 1).contiguous()


def resolve_vae_source_path() -> Path:
    for candidate in LOCAL_CACHE_CANDIDATES:
        if (candidate / "config.json").is_file() and (candidate / "diffusion_pytorch_model.safetensors").is_file():
            return candidate
    raise FileNotFoundError("Keine lokalen SD1.5 VAE-Gewichte gefunden.")


def deterministic_test_input() -> torch.Tensor:
    """Generate a reproducible, smooth 2D gradient test pattern in [-1.0, 1.0]."""
    y = torch.linspace(-1.0, 1.0, INPUT_SHAPE[2], dtype=torch.float32).view(1, 1, -1, 1)
    x = torch.linspace(-1.0, 1.0, INPUT_SHAPE[3], dtype=torch.float32).view(1, 1, 1, -1)
    r = x.expand(1, 1, INPUT_SHAPE[2], INPUT_SHAPE[3])
    g = y.expand(1, 1, INPUT_SHAPE[2], INPUT_SHAPE[3])
    b = ((x + y) * 0.5)
    return torch.cat((r, g, b), dim=1).contiguous()


def export_and_validate(
    output_onnx_path: Path = DEFAULT_TARGET_ONNX,
    validation_dir: Path = DEFAULT_VALIDATION_DIR,
) -> dict[str, Any]:
    output_onnx_path.parent.mkdir(parents=True, exist_ok=True)
    validation_dir.mkdir(parents=True, exist_ok=True)

    vae_dir = resolve_vae_source_path()
    weights_path = vae_dir / "diffusion_pytorch_model.safetensors"
    config_path = vae_dir / "config.json"

    print(f"Loading VAE from: {vae_dir}")
    print(f"Weights file: {weights_path} (size: {weights_path.stat().st_size} bytes)")
    weights_sha256 = sha256_file(weights_path)
    config_sha256 = sha256_file(config_path)
    print(f"Weights SHA256: {weights_sha256}")
    print(f"Config SHA256:  {config_sha256}")

    # Load configuration
    with open(config_path, "r", encoding="utf-8") as f:
        vae_config = json.load(f)

    # Validate exact SD1.5 architecture
    assert vae_config.get("sample_size") == 512, f"Unexpected sample_size: {vae_config.get('sample_size')}"
    assert vae_config.get("in_channels") == 3, f"Unexpected in_channels: {vae_config.get('in_channels')}"
    assert vae_config.get("latent_channels") == 4, f"Unexpected latent_channels: {vae_config.get('latent_channels')}"
    assert len(vae_config.get("down_block_types", [])) == 4, "Expected 4 down blocks"

    vae = AutoencoderKL.from_pretrained(vae_dir, local_files_only=True, torch_dtype=torch.float32)
    vae.eval()
    wrapper = SD15VAEEncoderExportWrapper(vae, scaling_factor=SCALING_FACTOR).eval()

    test_input = deterministic_test_input()
    print("Computing PyTorch reference output...")
    with torch.no_grad():
        ref_latent_1 = wrapper(test_input)
        ref_latent_2 = wrapper(test_input)

    # Check PyTorch determinism
    diff = (ref_latent_1 - ref_latent_2).abs().max().item()
    assert diff == 0.0, f"PyTorch forward pass is not bit-deterministic: diff={diff}"
    assert tuple(ref_latent_1.shape) == OUTPUT_SHAPE, f"Shape mismatch: {ref_latent_1.shape} != {OUTPUT_SHAPE}"

    ref_latent_np = ref_latent_1.detach().cpu().numpy()
    test_input_np = test_input.detach().cpu().numpy()

    # Save inputs and reference outputs as fixtures
    input_fixture_path = validation_dir / "vae_input_sample.npy"
    ref_fixture_path = validation_dir / "vae_latent_reference.npy"
    np.save(input_fixture_path, test_input_np, allow_pickle=False)
    np.save(ref_fixture_path, ref_latent_np, allow_pickle=False)

    print(f"Exporting ONNX model to: {output_onnx_path} (Opset {OPSET_VERSION})...")
    with torch.inference_mode():
        torch.onnx.export(
            wrapper,
            (test_input,),
            str(output_onnx_path),
            input_names=["image"],
            output_names=["latent"],
            opset_version=OPSET_VERSION,
            do_constant_folding=True,
            dynamic_axes=None,  # Static shapes: [1, 3, 512, 512] -> [1, 64, 64, 4]
            dynamo=False,
        )

    onnx_size_bytes = output_onnx_path.stat().st_size
    onnx_sha256 = sha256_file(output_onnx_path)
    print(f"ONNX Export successful! Size: {onnx_size_bytes} bytes, SHA256: {onnx_sha256}")

    # Validate ONNX Runtime inference
    import onnxruntime as ort

    print("Validating with ONNX Runtime CPUExecutionProvider...")
    ort_opts = ort.SessionOptions()
    ort_opts.intra_op_num_threads = 4
    ort_session = ort.InferenceSession(
        str(output_onnx_path), sess_options=ort_opts, providers=["CPUExecutionProvider"]
    )

    inputs_meta = ort_session.get_inputs()
    outputs_meta = ort_session.get_outputs()
    assert len(inputs_meta) == 1, f"Expected 1 input, got {len(inputs_meta)}"
    assert inputs_meta[0].name == "image", f"Expected input name 'image', got {inputs_meta[0].name}"
    assert list(inputs_meta[0].shape) == list(INPUT_SHAPE), f"Input shape mismatch: {inputs_meta[0].shape}"
    assert len(outputs_meta) == 1, f"Expected 1 output, got {len(outputs_meta)}"
    assert outputs_meta[0].name == "latent", f"Expected output name 'latent', got {outputs_meta[0].name}"
    assert list(outputs_meta[0].shape) == list(OUTPUT_SHAPE), f"Output shape mismatch: {outputs_meta[0].shape}"

    # Run inference
    ort_out_1 = ort_session.run(["latent"], {"image": test_input_np})[0]
    ort_out_2 = ort_session.run(["latent"], {"image": test_input_np})[0]

    # Check ORT determinism
    ort_diff = np.max(np.abs(ort_out_1 - ort_out_2))
    assert ort_diff == 0.0, f"ORT forward pass is not bit-deterministic: diff={ort_diff}"

    # Parity metrics: PyTorch vs ONNX Runtime
    abs_errors = np.abs(ort_out_1.astype(np.float64) - ref_latent_np.astype(np.float64))
    max_abs_error = float(np.max(abs_errors))
    mean_abs_error = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(abs_errors**2)))
    p99_error = float(np.percentile(abs_errors, 99.0))
    correlation = float(np.corrcoef(ort_out_1.flatten().astype(np.float64), ref_latent_np.flatten().astype(np.float64))[0, 1])

    print(f"Parity metrics:")
    print(f"  Max absolute error:  {max_abs_error:.6e}")
    print(f"  P99 absolute error:  {p99_error:.6e}")
    print(f"  Mean absolute error: {mean_abs_error:.6e}")
    print(f"  RMSE:                {rmse:.6e}")
    print(f"  Pearson correlation: {correlation:.8f}")

    # Standard FP32 deep CNN tolerances across GEMM backends
    assert max_abs_error < 1.5e-2, f"Parity failure: max_abs_error={max_abs_error} exceeds 0.015"
    assert mean_abs_error < 1e-3, f"Parity failure: mean_abs_error={mean_abs_error} exceeds 1e-3"
    assert correlation > 0.99999, f"Parity failure: correlation={correlation} below 0.99999"

    # Latent value range metrics
    latent_min = float(np.min(ort_out_1))
    latent_max = float(np.max(ort_out_1))
    latent_mean = float(np.mean(ort_out_1))
    latent_std = float(np.std(ort_out_1))
    print(f"Latent metrics on test input:")
    print(f"  Min:  {latent_min:.4f}")
    print(f"  Max:  {latent_max:.4f}")
    print(f"  Mean: {latent_mean:.4f}")
    print(f"  Std:  {latent_std:.4f}")

    results = {
        "model_id": "stable_diffusion_v1_5_vae_encoder",
        "target_file": str(output_onnx_path.resolve()),
        "target_size_bytes": onnx_size_bytes,
        "target_sha256": onnx_sha256,
        "source": {
            "repository": "runwayml/stable-diffusion-v1-5",
            "revision": "39593d5650112b4cc5804332986a22d7e502f811",
            "weights_file": str(weights_path),
            "weights_size_bytes": weights_path.stat().st_size,
            "weights_sha256": weights_sha256,
            "config_sha256": config_sha256,
        },
        "contract": {
            "input": {
                "name": "image",
                "shape": list(INPUT_SHAPE),
                "dtype": "float32",
                "layout": "NCHW",
                "normalization": "[-1.0, 1.0]",
            },
            "output": {
                "name": "latent",
                "shape": list(OUTPUT_SHAPE),
                "dtype": "float32",
                "layout": "NHWC",
                "scaling_factor": SCALING_FACTOR,
            },
            "opset_version": OPSET_VERSION,
            "static_shapes": True,
        },
        "validation": {
            "max_abs_error": max_abs_error,
            "p99_error": p99_error,
            "mean_abs_error": mean_abs_error,
            "rmse": rmse,
            "pearson_correlation": correlation,
            "pytorch_deterministic": True,
            "ort_deterministic": True,
            "parity_gate": "PASS",
            "test_latent_min": latent_min,
            "test_latent_max": latent_max,
            "test_latent_mean": latent_mean,
            "test_latent_std": latent_std,
        },
        "fixtures": {
            "input_sample": str(input_fixture_path.resolve()),
            "input_sample_sha256": sha256_file(input_fixture_path),
            "reference_latent": str(ref_fixture_path.resolve()),
            "reference_latent_sha256": sha256_file(ref_fixture_path),
        },
    }

    validation_json_path = validation_dir / "onnx_validation.json"
    with open(validation_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    manifest_json_path = validation_dir / "reference_manifest.json"
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "contract": results["contract"],
                "fixtures": results["fixtures"],
                "source": results["source"],
            },
            f,
            indent=2,
        )

    print(f"Validation manifest written to: {validation_json_path}")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_TARGET_ONNX, help="Output ONNX file path")
    parser.add_argument("--validation-dir", type=Path, default=DEFAULT_VALIDATION_DIR, help="Validation output directory")
    args = parser.parse_args()

    results = export_and_validate(output_onnx_path=args.output, validation_dir=args.validation_dir)
    print("SUCCESS: SD1.5 VAE Encoder export and validation completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
