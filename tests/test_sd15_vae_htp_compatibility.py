"""
Unit and Contract Tests for SD1.5 VAE Encoder / Decoder HTP Compatibility.
Sprint: IMG-EDIT-IMPL-16
Verifies:
1. Quantization parameter alignment across Encoder, Decoder, and UNet.
2. Strict Qualcomm Hexagon HTP execution (disable_cpu_ep_fallback = 1).
3. Mathematical equivalence of direct affine and two-step requantization.
4. E2E reconstruction quality gates (PSNR >= 28.0 dB, SSIM >= 0.85).
"""

from __future__ import annotations

import json
import os
import sys
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
HTP_ENCODER = PROTOTYPE_DIR / "vae_encoder_htp.onnx"
METADATA_JSON = PROTOTYPE_DIR / "metadata.json"

QNN_MODELS_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "HK NPU STUDIO" / "models" / "stable_diffusion_v1_5_qnn"
HTP_DECODER = QNN_MODELS_DIR / "vae.onnx"
QNN_METADATA_JSON = QNN_MODELS_DIR / "metadata.json"

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
    t1 = torch.from_numpy(img1_np).permute(2, 0, 1).unsqueeze(0).float()
    t2 = torch.from_numpy(img2_np).permute(2, 0, 1).unsqueeze(0).float()

    coords = torch.arange(11).float() - 5.0
    g = torch.exp(-(coords**2) / (2 * 1.5**2))
    g = g / g.sum()
    kernel = (g.unsqueeze(1) @ g.unsqueeze(0)).expand(3, 1, 11, 11)

    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu1 = F.conv2d(t1, kernel, padding=5, groups=3)
    mu2 = F.conv2d(t2, kernel, padding=5, groups=3)

    mu1_sq, mu2_sq, mu1_mu2 = mu1**2, mu2**2, mu1 * mu2
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


class SD15VAEHTPCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
        cls.devices = [d for d in ort.get_ep_devices() if d.ep_name == "QNNExecutionProvider"]
        cls.htp_backend = qnn.get_qnn_htp_path()
        cls.test_image_path = get_test_image_path()

        with open(METADATA_JSON, "r", encoding="utf-8") as f:
            cls.enc_meta = json.load(f)
        with open(QNN_METADATA_JSON, "r", encoding="utf-8") as f:
            cls.qnn_meta = json.load(f)

    def test_01_quantization_parameters_consistency(self) -> None:
        """Verify quantization parameters exist and match contract specifications."""
        enc_out = self.enc_meta["model_files"]["vae_encoder_htp.onnx"]["outputs"]["/Mul_1_output_0_QuantizeLinear"]["quantization_parameters"]
        dec_in = self.qnn_meta["model_files"]["vae.onnx"]["inputs"]["latent"]["quantization_parameters"]
        unet_in = self.qnn_meta["model_files"]["unet.onnx"]["inputs"]["latent"]["quantization_parameters"]

        self.assertAlmostEqual(float(enc_out["scale"]), 0.00012290581, places=7)
        self.assertEqual(int(enc_out["zero_point"]), 35417)

        self.assertAlmostEqual(float(dec_in["scale"]), 0.00034003707696683705, places=8)
        self.assertEqual(int(dec_in["zero_point"]), 34382)

        self.assertAlmostEqual(float(unet_in["scale"]), 0.00024176308943424374, places=8)
        self.assertEqual(int(unet_in["zero_point"]), 33983)

    def test_02_pure_htp_execution_without_cpu_fallback(self) -> None:
        """Verify both Encoder and Decoder execute with disable_cpu_ep_fallback = 1."""
        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        opts.add_provider_for_devices(self.devices, {"backend_path": self.htp_backend})

        sess_enc = ort.InferenceSession(str(HTP_ENCODER), sess_options=opts)
        sess_dec = ort.InferenceSession(str(HTP_DECODER), sess_options=opts)

        dummy_img = np.zeros((1, 512, 512, 3), dtype=np.uint16)
        dummy_lat = np.zeros((1, 64, 64, 4), dtype=np.uint16)

        out_enc = sess_enc.run(None, {"image_q_to_dq": dummy_img})[0]
        out_dec = sess_dec.run(None, {"latent": dummy_lat})[0]

        self.assertEqual(out_enc.shape, (1, 64, 64, 4))
        self.assertEqual(out_enc.dtype, np.uint16)
        self.assertEqual(out_dec.shape, (1, 512, 512, 3))
        self.assertEqual(out_dec.dtype, np.uint16)

    def test_03_mathematical_requantization_equivalence(self) -> None:
        """Verify two-step dequantize->requantize matches direct affine requantization."""
        s_enc = float(self.enc_meta["model_files"]["vae_encoder_htp.onnx"]["outputs"]["/Mul_1_output_0_QuantizeLinear"]["quantization_parameters"]["scale"])
        z_enc = int(self.enc_meta["model_files"]["vae_encoder_htp.onnx"]["outputs"]["/Mul_1_output_0_QuantizeLinear"]["quantization_parameters"]["zero_point"])
        s_dec = float(self.qnn_meta["model_files"]["vae.onnx"]["inputs"]["latent"]["quantization_parameters"]["scale"])
        z_dec = int(self.qnn_meta["model_files"]["vae.onnx"]["inputs"]["latent"]["quantization_parameters"]["zero_point"])

        test_q_enc = np.random.randint(0, 65536, size=(1, 64, 64, 4), dtype=np.uint16)

        # Method 1: Two-step
        lat_fp32 = (test_q_enc.astype(np.float32) - z_enc) * s_enc
        q_dec_two_step = np.clip(np.round(lat_fp32 / s_dec) + z_dec, 0, 65535).astype(np.uint16)

        # Method 2: Direct affine
        scale_ratio = s_enc / s_dec
        q_dec_direct = np.clip(np.round((test_q_enc.astype(np.float32) - z_enc) * scale_ratio) + z_dec, 0, 65535).astype(np.uint16)

        max_diff = int(np.max(np.abs(q_dec_two_step.astype(np.int32) - q_dec_direct.astype(np.int32))))
        self.assertLessEqual(max_diff, 1, f"Requantization discrepancy too large: {max_diff} LSB")

    def test_04_e2e_reconstruction_quality_gate(self) -> None:
        """Verify End-to-End reconstruction quality meets PSNR >= 28 dB and SSIM >= 0.85."""
        with Image.open(self.test_image_path) as opened:
            orig_pil = opened.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
        orig_np = np.array(orig_pil, dtype=np.uint8)
        arr = (orig_np.astype(np.float32) / 255.0) * 2.0 - 1.0

        # Load metadata params
        img_scale = float(self.enc_meta["model_files"]["vae_encoder_htp.onnx"]["inputs"]["image_q_to_dq"]["quantization_parameters"]["scale"])
        img_zp = int(self.enc_meta["model_files"]["vae_encoder_htp.onnx"]["inputs"]["image_q_to_dq"]["quantization_parameters"]["zero_point"])
        s_enc = float(self.enc_meta["model_files"]["vae_encoder_htp.onnx"]["outputs"]["/Mul_1_output_0_QuantizeLinear"]["quantization_parameters"]["scale"])
        z_enc = int(self.enc_meta["model_files"]["vae_encoder_htp.onnx"]["outputs"]["/Mul_1_output_0_QuantizeLinear"]["quantization_parameters"]["zero_point"])
        s_dec = float(self.qnn_meta["model_files"]["vae.onnx"]["inputs"]["latent"]["quantization_parameters"]["scale"])
        z_dec = int(self.qnn_meta["model_files"]["vae.onnx"]["inputs"]["latent"]["quantization_parameters"]["zero_point"])

        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        opts.add_provider_for_devices(self.devices, {"backend_path": self.htp_backend})

        # 1. HTP Encoder Run
        sess_enc = ort.InferenceSession(str(HTP_ENCODER), sess_options=opts)
        in_nhwc = arr[np.newaxis, ...]
        in_uint16 = np.clip(np.round(in_nhwc / img_scale) + img_zp, 0, 65535).astype(np.uint16)
        enc_out = sess_enc.run(None, {"image_q_to_dq": in_uint16})[0]

        # 2. Dequantize to Latent FP32 & Requantize to Decoder UINT16
        latent_fp32 = (enc_out.astype(np.float32) - z_enc) * s_enc
        dec_in = np.clip(np.round(latent_fp32 / s_dec) + z_dec, 0, 65535).astype(np.uint16)

        # 3. HTP Decoder Run
        sess_dec = ort.InferenceSession(str(HTP_DECODER), sess_options=opts)
        dec_out = sess_dec.run(None, {"latent": dec_in})[0]
        recon_np = (dec_out[0] * (255.0 / 65535.0)).astype(np.uint8)

        # 4. Reference CPU Encoder Run
        sess_cpu = ort.InferenceSession(str(FP32_CPU_ENCODER), providers=["CPUExecutionProvider"])
        in_nchw = np.transpose(arr, (2, 0, 1))[np.newaxis, ...]
        cpu_latent = sess_cpu.run(None, {"image": in_nchw})[0]
        cpu_dec_in = np.clip(np.round(cpu_latent / s_dec) + z_dec, 0, 65535).astype(np.uint16)
        cpu_dec_out = sess_dec.run(None, {"latent": cpu_dec_in})[0]
        cpu_recon_np = (cpu_dec_out[0] * (255.0 / 65535.0)).astype(np.uint8)

        # Compare metrics
        psnr_vs_cpu = compute_psnr(cpu_recon_np, recon_np)
        ssim_vs_cpu = compute_ssim_torch(cpu_recon_np, recon_np)

        print(f"\n[E2E Parity Validation Metrics]")
        print(f"  PSNR (HTP vs CPU Pipeline): {psnr_vs_cpu:.2f} dB (Gate >= 28.0 dB)")
        print(f"  SSIM (HTP vs CPU Pipeline): {ssim_vs_cpu:.4f} (Gate >= 0.85)")

        self.assertGreaterEqual(psnr_vs_cpu, 28.0, f"PSNR {psnr_vs_cpu:.2f} dB is below gate 28.0 dB")
        self.assertGreaterEqual(ssim_vs_cpu, 0.85, f"SSIM {ssim_vs_cpu:.4f} is below gate 0.85")


if __name__ == "__main__":
    unittest.main()
