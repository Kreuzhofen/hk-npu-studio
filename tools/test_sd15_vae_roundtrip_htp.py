"""
End-to-End Reconstruction Test: CPU VAE Encoder -> Qualcomm Hexagon HTP VAE Decoder.
Evaluates Stable Diffusion 1.5 VAE Roundtrip on Windows ARM64.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import onnxruntime as ort
import onnxruntime_qnn as qnn
import torch
import torch.nn.functional as F
from PIL import Image

DEFAULT_ENCODER_PATH = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn" / "vae_encoder.onnx"
DEFAULT_QNN_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "HK NPU STUDIO" / "models" / "stable_diffusion_v1_5_qnn"
DEFAULT_TEST_IMAGE = REPO_ROOT / "temp" / "sd15_first_npu_image" / "first_sd15_npu.png"
OUTPUT_DIR = REPO_ROOT / "temp" / "sd15_vae_roundtrip_htp"


def sha256_file(path: str | Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_ssim_torch(img1_np: np.ndarray, img2_np: np.ndarray) -> float:
    """
    Compute textbook SSIM (Wang et al., 2004) on RGB images in [0, 255].
    img1_np, img2_np: uint8 or float32 arrays of shape [H, W, 3].
    """
    t1 = torch.from_numpy(img1_np).permute(2, 0, 1).unsqueeze(0).float()
    t2 = torch.from_numpy(img2_np).permute(2, 0, 1).unsqueeze(0).float()

    # 11x11 Gaussian filter with sigma=1.5
    coords = torch.arange(11).float() - 5.0
    g = torch.exp(-(coords**2) / (2 * 1.5**2))
    g = g / g.sum()
    kernel_2d = g.unsqueeze(1) @ g.unsqueeze(0)
    kernel = kernel_2d.expand(3, 1, 11, 11)

    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu1 = F.conv2d(t1, kernel, padding=5, groups=3)
    mu2 = F.conv2d(t2, kernel, padding=5, groups=3)

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = F.conv2d(t1 * t1, kernel, padding=5, groups=3) - mu1_sq
    sigma2_sq = F.conv2d(t2 * t2, kernel, padding=5, groups=3) - mu2_sq
    sigma12 = F.conv2d(t1 * t2, kernel, padding=5, groups=3) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / (
        (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
    )
    return float(ssim_map.mean().item())


def compute_metrics(orig_rgb: np.ndarray, recon_rgb: np.ndarray) -> dict[str, float]:
    diff = np.abs(orig_rgb.astype(np.float64) - recon_rgb.astype(np.float64))
    mae = float(np.mean(diff))
    mae_norm = mae / 255.0
    mse = float(np.mean(diff**2))
    if mse == 0.0:
        psnr = 100.0
    else:
        psnr = float(10.0 * np.log10((255.0**2) / mse))
    ssim = compute_ssim_torch(orig_rgb, recon_rgb)
    return {
        "mae_pixel_0_255": mae,
        "mae_normalized_0_1": mae_norm,
        "mse": mse,
        "psnr_db": psnr,
        "ssim": ssim,
    }


def run_roundtrip_test(
    encoder_path: Path = DEFAULT_ENCODER_PATH,
    qnn_dir: Path = DEFAULT_QNN_DIR,
    test_image_path: Path = DEFAULT_TEST_IMAGE,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("SD1.5 VAE Roundtrip Test: CPU Encoder -> Qualcomm Hexagon HTP Decoder")
    print("=" * 80)

    # 1. Validate inputs and environment
    assert encoder_path.is_file(), f"Encoder not found: {encoder_path}"
    assert qnn_dir.is_dir(), f"QNN dir not found: {qnn_dir}"
    assert test_image_path.is_file(), f"Test image not found: {test_image_path}"

    decoder_onnx_path = qnn_dir / "vae.onnx"
    decoder_context_path = qnn_dir / "vae_qairt_context.bin"
    metadata_json_path = qnn_dir / "metadata.json"

    assert decoder_onnx_path.is_file(), f"Decoder ONNX not found: {decoder_onnx_path}"
    assert decoder_context_path.is_file(), f"Decoder context bin not found: {decoder_context_path}"
    assert metadata_json_path.is_file(), f"metadata.json not found: {metadata_json_path}"

    encoder_sha256 = sha256_file(encoder_path)
    decoder_onnx_sha256 = sha256_file(decoder_onnx_path)
    decoder_context_sha256 = sha256_file(decoder_context_path)
    test_image_sha256 = sha256_file(test_image_path)

    print(f"Encoder ONNX:        {encoder_path} (size: {encoder_path.stat().st_size} bytes)")
    print(f"  SHA-256:           {encoder_sha256}")
    print(f"Decoder ONNX:        {decoder_onnx_path} (size: {decoder_onnx_path.stat().st_size} bytes)")
    print(f"  SHA-256:           {decoder_onnx_sha256}")
    print(f"Decoder Context Bin: {decoder_context_path} (size: {decoder_context_path.stat().st_size} bytes)")
    print(f"  SHA-256:           {decoder_context_sha256}")
    print(f"Test Image:          {test_image_path}")
    print(f"  SHA-256:           {test_image_sha256}")

    # 2. Read QNN Decoder Metadata
    with open(metadata_json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    vae_meta = meta["model_files"]["vae.onnx"]
    scale_in = float(vae_meta["inputs"]["latent"]["quantization_parameters"]["scale"])
    zp_in = int(vae_meta["inputs"]["latent"]["quantization_parameters"]["zero_point"])
    scale_out = float(vae_meta["outputs"]["image"]["quantization_parameters"]["scale"])
    zp_out = int(vae_meta["outputs"]["image"]["quantization_parameters"]["zero_point"])

    print(f"\nQNN Decoder Metadata:")
    print(f"  Input Latent Quant:  scale={scale_in}, zero_point={zp_in}, shape={vae_meta['inputs']['latent']['shape']}")
    print(f"  Output Image Quant:  scale={scale_out}, zero_point={zp_out}, shape={vae_meta['outputs']['image']['shape']}")

    # 3. Load and preprocess test image
    orig_img = Image.open(test_image_path).convert("RGB")
    assert orig_img.size == (512, 512), f"Expected 512x512 image, got {orig_img.size}"
    orig_np = np.array(orig_img, dtype=np.uint8)

    # Normalize RGB to [-1.0, 1.0] in NCHW
    img_norm = (orig_np.astype(np.float32) / 255.0) * 2.0 - 1.0
    img_nchw = np.transpose(img_norm, (2, 0, 1))[np.newaxis, ...]  # [1, 3, 512, 512]

    # 4. CPU VAE Encoder Inference
    print(f"\n[1/3] Running VAE Encoder on CPU (ONNX Runtime CPUExecutionProvider)...")
    enc_opts = ort.SessionOptions()
    enc_opts.intra_op_num_threads = 4
    enc_session = ort.InferenceSession(str(encoder_path), sess_options=enc_opts, providers=["CPUExecutionProvider"])

    t_enc_start = time.perf_counter()
    latent_float = enc_session.run(["latent"], {"image": img_nchw})[0]
    t_enc_ms = (time.perf_counter() - t_enc_start) * 1000.0

    print(f"  Encoder execution time: {t_enc_ms:.2f} ms")
    print(f"  Latent Shape:          {latent_float.shape}")
    print(f"  Latent Dtype:          {latent_float.dtype}")
    print(f"  Latent Min:            {float(np.min(latent_float)):.4f}")
    print(f"  Latent Max:            {float(np.max(latent_float)):.4f}")
    print(f"  Latent Mean:           {float(np.mean(latent_float)):.4f}")
    print(f"  Latent Std:            {float(np.std(latent_float)):.4f}")

    assert latent_float.shape == (1, 64, 64, 4), f"Shape mismatch: {latent_float.shape}"
    assert latent_float.dtype == np.float32, f"Dtype mismatch: {latent_float.dtype}"

    # 5. Quantize Latent according to QNN Decoder metadata
    print(f"\n[2/3] Quantizing Latent tensor for QNN Decoder...")
    latent_quant = np.clip(np.round(latent_float / scale_in) + zp_in, 0, 65535).astype(np.uint16)
    print(f"  Quantized Latent Min:  {int(np.min(latent_quant))}")
    print(f"  Quantized Latent Max:  {int(np.max(latent_quant))}")
    print(f"  Quantized Latent Mean: {float(np.mean(latent_quant)):.2f}")

    # 6. Setup Qualcomm QNN HTP Session
    print(f"\n[3/3] Setting up Qualcomm Hexagon HTP V73 QNN Session...")
    ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
    all_devices = ort.get_ep_devices()
    selected_devices = [d for d in all_devices if d.ep_name == "QNNExecutionProvider"]
    assert selected_devices, "No QNNExecutionProvider devices found in get_ep_devices()"

    qnn_opts = ort.SessionOptions()
    # Explicitly enforce NO CPU FALLBACK
    qnn_opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    provider_options = {"backend_path": qnn.get_qnn_htp_path()}
    qnn_opts.add_provider_for_devices(selected_devices, provider_options)

    print(f"  Loading {decoder_onnx_path.name} on Qualcomm Hexagon HTP...")
    t_load_start = time.perf_counter()
    dec_session = ort.InferenceSession(str(decoder_onnx_path), sess_options=qnn_opts)
    t_load_ms = (time.perf_counter() - t_load_start) * 1000.0
    print(f"  HTP Session created in: {t_load_ms:.2f} ms")

    # Run decoder on HTP
    print(f"  Executing VAE Decoder inference on Qualcomm Hexagon HTP...")
    t_dec_start = time.perf_counter()
    image_quant = dec_session.run(["image"], {"latent": latent_quant})[0]
    t_dec_ms = (time.perf_counter() - t_dec_start) * 1000.0
    print(f"  Decoder execution time: {t_dec_ms:.2f} ms on Hexagon HTP")

    # 7. Dequantize output image
    image_float = (image_quant.astype(np.float32) - zp_out) * scale_out
    recon_rgb = np.clip(image_float[0] * 255.0, 0, 255).astype(np.uint8)

    # 8. Compute quality metrics
    metrics = compute_metrics(orig_np, recon_rgb)

    print(f"\nReconstruction Quality Metrics (Original vs. Reconstructed):")
    print(f"  PSNR:     {metrics['psnr_db']:.2f} dB (Target: >= 28.0 dB)")
    print(f"  SSIM:     {metrics['ssim']:.4f} (Target: >= 0.8500)")
    print(f"  MAE (px): {metrics['mae_pixel_0_255']:.2f} / 255")
    print(f"  MSE:      {metrics['mse']:.2f}")

    target_psnr_met = metrics["psnr_db"] >= 28.0
    target_ssim_met = metrics["ssim"] >= 0.85
    gate_status = "PASS" if (target_psnr_met and target_ssim_met) else "FAIL"

    print(f"\nQuality Target Evaluation:")
    print(f"  PSNR >= 28 dB: {target_psnr_met} ({metrics['psnr_db']:.2f} dB)")
    print(f"  SSIM >= 0.85:  {target_ssim_met} ({metrics['ssim']:.4f})")
    print(f"  Overall Gate:  {gate_status}")

    # 9. Save Reconstructed Image and Comparison Grid
    recon_img_path = output_dir / "reconstructed_image.png"
    Image.fromarray(recon_rgb).save(recon_img_path)

    # Create side-by-side comparison
    comparison = Image.new("RGB", (1024, 512))
    comparison.paste(orig_img, (0, 0))
    comparison.paste(Image.fromarray(recon_rgb), (512, 0))
    comparison_path = output_dir / "roundtrip_comparison.png"
    comparison.save(comparison_path)

    # Absolute difference heatmap
    diff_vis = np.clip(np.abs(orig_np.astype(np.float32) - recon_rgb.astype(np.float32)) * 3.0, 0, 255).astype(np.uint8)
    diff_path = output_dir / "difference_amplified_3x.png"
    Image.fromarray(diff_vis).save(diff_path)

    report = {
        "sprint": "IMG-EDIT-IMPL-06",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_image": {
            "path": str(test_image_path.resolve()),
            "size": list(orig_img.size),
            "sha256": test_image_sha256,
        },
        "encoder": {
            "path": str(encoder_path.resolve()),
            "sha256": encoder_sha256,
            "runtime": "CPU (ONNX Runtime CPUExecutionProvider)",
            "execution_ms": t_enc_ms,
            "latent_shape": list(latent_float.shape),
            "latent_stats": {
                "min": float(np.min(latent_float)),
                "max": float(np.max(latent_float)),
                "mean": float(np.mean(latent_float)),
                "std": float(np.std(latent_float)),
            },
        },
        "decoder": {
            "path": str(decoder_onnx_path.resolve()),
            "context_bin_path": str(decoder_context_path.resolve()),
            "onnx_sha256": decoder_onnx_sha256,
            "context_sha256": decoder_context_sha256,
            "runtime": "Qualcomm Hexagon HTP V73 via QNN EP",
            "disable_cpu_fallback": True,
            "execution_ms": t_dec_ms,
            "quantization_parameters": {
                "input_scale": scale_in,
                "input_zero_point": zp_in,
                "output_scale": scale_out,
                "output_zero_point": zp_out,
            },
        },
        "metrics": metrics,
        "targets": {
            "target_psnr_db": 28.0,
            "target_ssim": 0.85,
            "psnr_target_met": target_psnr_met,
            "ssim_target_met": target_ssim_met,
            "gate_status": gate_status,
        },
        "artifacts": {
            "reconstructed_image": str(recon_img_path.resolve()),
            "reconstructed_image_sha256": sha256_file(recon_img_path),
            "comparison_image": str(comparison_path.resolve()),
            "difference_heatmap": str(diff_path.resolve()),
        },
        "htp_verification": {
            "qnn_devices_count": len(selected_devices),
            "disable_cpu_ep_fallback_enforced": True,
            "qnn_lib_path": qnn.get_library_path(),
            "qnn_htp_dll": qnn.get_qnn_htp_path(),
        },
    }

    report_json_path = output_dir / "roundtrip_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nArtifacts written to: {output_dir}")
    print(f"  Reconstructed Image: {recon_img_path}")
    print(f"  Comparison Grid:     {comparison_path}")
    print(f"  Report JSON:         {report_json_path}")
    print("=" * 80)
    return report


if __name__ == "__main__":
    run_roundtrip_test()
