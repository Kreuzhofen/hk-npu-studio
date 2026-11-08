"""
Integration and validation tests for SD1.5 VAE Encoder Qualcomm Hexagon HTP prototype.
Verifies:
1. Model prototype artifacts existence and integrity.
2. Hexagon HTP execution with disable_cpu_ep_fallback = 1.
3. Latent and image reconstruction quality (PSNR >= 28 dB, SSIM >= 0.85).
4. Warm inference latency measurement.
"""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F
import onnxruntime as ort
import onnxruntime_qnn as qnn

PROTOTYPE_DIR = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn" / "prototype"
FP32_CPU_ENCODER = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn" / "vae_encoder.onnx"
NHWC_MODEL = PROTOTYPE_DIR / "vae_encoder_nhwc.onnx"
QDQ_MODEL = PROTOTYPE_DIR / "vae_encoder_w8a16_qdq.onnx"
HTP_MODEL = PROTOTYPE_DIR / "vae_encoder_htp.onnx"
HTP_BIN = PROTOTYPE_DIR / "vae_encoder_htp_qnn.bin"

DECODER_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "HK NPU STUDIO" / "models" / "stable_diffusion_v1_5_qnn"
DECODER_MODEL = DECODER_DIR / "vae.onnx"

# Quantization parameters from calibration metadata
IMG_SCALE = 3.0518044e-05
IMG_ZP = 32768
LAT_SCALE = 0.00012290581
LAT_ZP = 35417

TEST_IMAGE_CANDIDATES = [
    REPO_ROOT / "temp" / "sd15_first_npu_image" / "first_sd15_npu.png",
    REPO_ROOT / "sd15_inpainting_test_artifacts" / "inpaint_input.png",
    REPO_ROOT / "temp" / "sd15_inpainting_test_artifacts" / "inpaint_input.png",
]


def get_test_image_path() -> Path:
    for p in TEST_IMAGE_CANDIDATES:
        if p.is_file():
            return p
    raise FileNotFoundError("No valid 512x512 test image found in candidates.")


def compute_ssim_torch(img1_np: np.ndarray, img2_np: np.ndarray) -> float:
    """Wang et al. 2004 SSIM implementation using PyTorch Gaussian convolution."""
    t1 = torch.from_numpy(img1_np).permute(2, 0, 1).unsqueeze(0).float()
    t2 = torch.from_numpy(img2_np).permute(2, 0, 1).unsqueeze(0).float()

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


def compute_psnr(img1_np: np.ndarray, img2_np: np.ndarray) -> float:
    diff = img1_np.astype(np.float64) - img2_np.astype(np.float64)
    mse = float(np.mean(diff**2))
    if mse == 0.0:
        return 100.0
    return float(10.0 * np.log10((255.0**2) / mse))


class SD15VAEEncoderHTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
        cls.devices = [d for d in ort.get_ep_devices() if d.ep_name == "QNNExecutionProvider"]
        cls.htp_backend = qnn.get_qnn_htp_path()
        cls.test_image_path = get_test_image_path()

    def test_01_prototype_artifacts_exist(self) -> None:
        """Verify all prototype artifacts are present and non-empty."""
        self.assertTrue(FP32_CPU_ENCODER.is_file(), f"Missing CPU reference: {FP32_CPU_ENCODER}")
        self.assertTrue(NHWC_MODEL.is_file(), f"Missing NHWC model: {NHWC_MODEL}")
        self.assertTrue(QDQ_MODEL.is_file(), f"Missing QDQ model: {QDQ_MODEL}")
        self.assertTrue(HTP_MODEL.is_file(), f"Missing HTP ONNX model: {HTP_MODEL}")
        self.assertTrue(HTP_BIN.is_file(), f"Missing HTP context binary: {HTP_BIN}")

        self.assertGreater(NHWC_MODEL.stat().st_size, 100 * 1024 * 1024)
        self.assertGreater(QDQ_MODEL.stat().st_size, 30 * 1024 * 1024)
        self.assertGreater(HTP_MODEL.stat().st_size, 500)
        self.assertGreater(HTP_BIN.stat().st_size, 100 * 1024 * 1024)

    def test_02_pure_htp_execution_without_cpu_fallback(self) -> None:
        """Verify model executes on Qualcomm Hexagon HTP with disable_cpu_ep_fallback = 1."""
        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        provider_options = {"backend_path": self.htp_backend}
        opts.add_provider_for_devices(self.devices, provider_options)

        session = ort.InferenceSession(str(HTP_MODEL), sess_options=opts)
        dummy_uint16 = np.zeros((1, 512, 512, 3), dtype=np.uint16)

        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        out = session.run([output_name], {input_name: dummy_uint16})[0]

        self.assertEqual(out.shape, (1, 64, 64, 4))
        self.assertEqual(out.dtype, np.uint16)

    def test_03_reconstruction_quality_psnr_ssim(self) -> None:
        """
        Verify HTP prototype produces latents matching CPU reference within quality gates:
        PSNR >= 28.0 dB, SSIM >= 0.85.
        """
        with Image.open(self.test_image_path) as opened:
            img = opened.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
        arr = (np.array(img, dtype=np.float32) / 255.0) * 2.0 - 1.0

        # 1. Run FP32 CPU reference
        sess_cpu = ort.InferenceSession(str(FP32_CPU_ENCODER), providers=["CPUExecutionProvider"])
        in_nchw = np.transpose(arr, (2, 0, 1))[np.newaxis, ...]
        cpu_latent = sess_cpu.run(["latent"], {"image": in_nchw})[0]

        # 2. Run HTP Prototype
        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        opts.add_provider_for_devices(self.devices, {"backend_path": self.htp_backend})
        sess_htp = ort.InferenceSession(str(HTP_MODEL), sess_options=opts)

        in_nhwc = arr[np.newaxis, ...]
        in_uint16 = np.clip(np.round(in_nhwc / IMG_SCALE) + IMG_ZP, 0, 65535).astype(np.uint16)

        input_name = sess_htp.get_inputs()[0].name
        output_name = sess_htp.get_outputs()[0].name
        htp_out_uint16 = sess_htp.run([output_name], {input_name: in_uint16})[0]
        htp_latent = (htp_out_uint16.astype(np.float32) - LAT_ZP) * LAT_SCALE

        # 3. Latent comparison metrics
        latent_diff = np.abs(cpu_latent - htp_latent)
        latent_mae = float(np.mean(latent_diff))
        latent_mse = float(np.mean(latent_diff**2))
        latent_psnr = float(10.0 * np.log10((float(np.max(cpu_latent) - np.min(cpu_latent)) ** 2) / latent_mse))

        # 4. Decode both latents through Qualcomm Hexagon HTP VAE Decoder
        sess_dec = ort.InferenceSession(str(DECODER_MODEL), sess_options=opts)
        dec_scale = 0.00034003707696683705
        dec_zp = 34382

        cpu_q = np.clip(np.round(cpu_latent / dec_scale) + dec_zp, 0, 65535).astype(np.uint16)
        htp_q = np.clip(np.round(htp_latent / dec_scale) + dec_zp, 0, 65535).astype(np.uint16)

        dec_cpu = sess_dec.run(["image"], {"latent": cpu_q})[0]
        dec_htp = sess_dec.run(["image"], {"latent": htp_q})[0]

        img_cpu = (dec_cpu[0] * (255.0 / 65535.0)).astype(np.uint8)
        img_htp = (dec_htp[0] * (255.0 / 65535.0)).astype(np.uint8)

        psnr_val = compute_psnr(img_cpu, img_htp)
        ssim_val = compute_ssim_torch(img_cpu, img_htp)

        print(f"\n[Validation Quality Metrics]")
        print(f"  Latent MAE:         {latent_mae:.6f}")
        print(f"  Latent MSE:         {latent_mse:.6f}")
        print(f"  Latent PSNR:        {latent_psnr:.2f} dB")
        print(f"  Decoded Image PSNR: {psnr_val:.2f} dB (Required >= 28.0 dB)")
        print(f"  Decoded Image SSIM: {ssim_val:.4f} (Required >= 0.85)")

        self.assertGreaterEqual(psnr_val, 28.0, f"PSNR {psnr_val:.2f} dB is below gate 28.0 dB")
        self.assertGreaterEqual(ssim_val, 0.85, f"SSIM {ssim_val:.4f} is below gate 0.85")

    def test_04_warm_htp_latency(self) -> None:
        """Measure warm inference latency on Hexagon HTP across 3 runs."""
        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        opts.add_provider_for_devices(self.devices, {"backend_path": self.htp_backend})
        session = ort.InferenceSession(str(HTP_MODEL), sess_options=opts)

        dummy = np.zeros((1, 512, 512, 3), dtype=np.uint16)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name

        # Warmup run
        _ = session.run([output_name], {input_name: dummy})

        runs_ms: list[float] = []
        for _ in range(3):
            t0 = time.perf_counter()
            _ = session.run([output_name], {input_name: dummy})
            dur_ms = (time.perf_counter() - t0) * 1000.0
            runs_ms.append(dur_ms)

        mean_ms = sum(runs_ms) / len(runs_ms)
        print(f"\n[Warm Latency Metrics]")
        print(f"  Runs (ms): {[f'{r:.1f}' for r in runs_ms]}")
        print(f"  Mean (ms): {mean_ms:.1f} ms (~{mean_ms/1000.0:.2f} s)")

        # Verify inference succeeds and produces valid latency
        self.assertGreater(mean_ms, 0.0)
        self.assertLess(mean_ms, 10000.0)  # Must be faster than 10s (CPU is 18.3s)


if __name__ == "__main__":
    unittest.main()
