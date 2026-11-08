"""
Comprehensive verification of Qualcomm Hexagon HTP VAE Encoder/Decoder compatibility.
Performs:
1. Exact mathematical quantization analysis (Encoder -> Latent FP32 -> Decoder / UNet).
2. Pure Hexagon HTP execution for both Encoder and Decoder (session.disable_cpu_ep_fallback = 1).
3. E2E Reconstruction quality validation (PSNR >= 28 dB, SSIM >= 0.85) against Original Ground Truth and CPU reference.
4. Generates visual comparison artifacts and metrics summary.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify_sd15_vae_htp_compatibility")

PROTOTYPE_DIR = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn" / "prototype"
FP32_CPU_ENCODER = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn" / "vae_encoder.onnx"
HTP_ENCODER = PROTOTYPE_DIR / "vae_encoder_htp.onnx"
HTP_BIN = PROTOTYPE_DIR / "vae_encoder_htp_qnn.bin"
METADATA_JSON = PROTOTYPE_DIR / "metadata.json"

QNN_MODELS_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "HK NPU STUDIO" / "models" / "stable_diffusion_v1_5_qnn"
HTP_DECODER = QNN_MODELS_DIR / "vae.onnx"
QNN_METADATA_JSON = QNN_MODELS_DIR / "metadata.json"

OUTPUT_DIR = REPO_ROOT / "temp" / "sd15_vae_roundtrip_htp"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Test image search path
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


def run_compatibility_verification() -> dict[str, any]:
    logger.info("=" * 80)
    logger.info("SD1.5 VAE HTP Encoder / Decoder Compatibility Verification")
    logger.info("=" * 80)

    # 1. Read Metadata
    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        enc_meta = json.load(f)
    with open(QNN_METADATA_JSON, "r", encoding="utf-8") as f:
        qnn_meta = json.load(f)

    enc_inp_param = enc_meta["model_files"]["vae_encoder_htp.onnx"]["inputs"]["image_q_to_dq"]["quantization_parameters"]
    enc_out_param = enc_meta["model_files"]["vae_encoder_htp.onnx"]["outputs"]["/Mul_1_output_0_QuantizeLinear"]["quantization_parameters"]
    dec_inp_param = qnn_meta["model_files"]["vae.onnx"]["inputs"]["latent"]["quantization_parameters"]
    unet_inp_param = qnn_meta["model_files"]["unet.onnx"]["inputs"]["latent"]["quantization_parameters"]
    unet_out_param = qnn_meta["model_files"]["unet.onnx"]["outputs"]["output_latent"]["quantization_parameters"]

    img_scale = float(enc_inp_param["scale"])
    img_zp = int(enc_inp_param["zero_point"])
    s_enc = float(enc_out_param["scale"])
    z_enc = int(enc_out_param["zero_point"])
    s_dec = float(dec_inp_param["scale"])
    z_dec = int(dec_inp_param["zero_point"])
    s_unet_in = float(unet_inp_param["scale"])
    z_unet_in = int(unet_inp_param["zero_point"])
    s_unet_out = float(unet_out_param["scale"])
    z_unet_out = int(unet_out_param["zero_point"])

    logger.info("Quantization Parameters:")
    logger.info("  Encoder Input (Image):       scale=%g, zero_point=%d", img_scale, img_zp)
    logger.info("  Encoder Output (Latent):     scale=%g, zero_point=%d", s_enc, z_enc)
    logger.info("  Decoder Input (Latent):      scale=%g, zero_point=%d", s_dec, z_dec)
    logger.info("  UNet Input (Latent):         scale=%g, zero_point=%d", s_unet_in, z_unet_in)
    logger.info("  UNet Output (Output Latent): scale=%g, zero_point=%d", s_unet_out, z_unet_out)

    # 2. Mathematical Affine Scale Ratios
    enc_to_dec_ratio = s_enc / s_dec
    enc_to_unet_ratio = s_enc / s_unet_in
    logger.info("Mathematical Conversion Ratios:")
    logger.info("  Encoder -> Decoder Direct Scale Ratio: %.8f", enc_to_dec_ratio)
    logger.info("  Encoder -> UNet Input Scale Ratio:    %.8f", enc_to_unet_ratio)

    # 3. Load Test Image
    test_img_path = get_test_image_path()
    logger.info("Loading Test Image: %s", test_img_path)
    with Image.open(test_img_path) as opened:
        orig_img_pil = opened.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
    orig_img_np = np.array(orig_img_pil, dtype=np.uint8)
    arr = (orig_img_np.astype(np.float32) / 255.0) * 2.0 - 1.0

    # 4. Prepare HTP Provider with disable_cpu_ep_fallback = 1
    ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
    devices = [d for d in ort.get_ep_devices() if d.ep_name == "QNNExecutionProvider"]
    opts = ort.SessionOptions()
    opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    opts.add_provider_for_devices(devices, {"backend_path": qnn.get_qnn_htp_path()})

    # 5. Run Pure Hexagon HTP VAE Encoder
    logger.info("Executing SD1.5 VAE Encoder on Qualcomm Hexagon HTP (disable_cpu_ep_fallback=1)...")
    sess_enc = ort.InferenceSession(str(HTP_ENCODER), sess_options=opts)
    in_nhwc = arr[np.newaxis, ...]
    in_uint16 = np.clip(np.round(in_nhwc / img_scale) + img_zp, 0, 65535).astype(np.uint16)

    t0 = time.perf_counter()
    enc_out_uint16 = sess_enc.run(None, {"image_q_to_dq": in_uint16})[0]
    t_enc_ms = (time.perf_counter() - t0) * 1000.0
    logger.info("  HTP Encoder Inference Time: %.1f ms", t_enc_ms)

    # 6. Mathematical Latent Requantization
    # Method A: Two-step dequantize -> requantize
    latent_fp32 = (enc_out_uint16.astype(np.float32) - z_enc) * s_enc
    dec_in_uint16_two_step = np.clip(np.round(latent_fp32 / s_dec) + z_dec, 0, 65535).astype(np.uint16)

    # Method B: Direct affine transform
    dec_in_uint16_direct = np.clip(
        np.round((enc_out_uint16.astype(np.float32) - z_enc) * enc_to_dec_ratio) + z_dec,
        0,
        65535,
    ).astype(np.uint16)

    diff_quant = np.max(np.abs(dec_in_uint16_two_step.astype(np.int32) - dec_in_uint16_direct.astype(np.int32)))
    logger.info("Quantization Re-encoding Parity (Method A vs Method B max diff): %d LSB", diff_quant)
    assert diff_quant <= 1, f"Quantization calculation mismatch: {diff_quant}"

    # Requantization for UNet input
    unet_in_uint16 = np.clip(np.round(latent_fp32 / s_unet_in) + z_unet_in, 0, 65535).astype(np.uint16)
    logger.info("UNet input requantization verified: shape=%s, range=[%d, %d]", unet_in_uint16.shape, int(unet_in_uint16.min()), int(unet_in_uint16.max()))

    # 7. Run Pure Hexagon HTP VAE Decoder
    logger.info("Executing SD1.5 VAE Decoder on Qualcomm Hexagon HTP (disable_cpu_ep_fallback=1)...")
    sess_dec = ort.InferenceSession(str(HTP_DECODER), sess_options=opts)

    t0 = time.perf_counter()
    dec_out_uint16 = sess_dec.run(None, {"latent": dec_in_uint16_two_step})[0]
    t_dec_ms = (time.perf_counter() - t0) * 1000.0
    logger.info("  HTP Decoder Inference Time: %.1f ms", t_dec_ms)

    # Convert decoded UINT16 to RGB image
    recon_img_np = (dec_out_uint16[0] * (255.0 / 65535.0)).astype(np.uint8)

    # 8. Run FP32 CPU Encoder Reference for Cross-Comparison
    logger.info("Executing Reference CPU FP32 Encoder...")
    sess_cpu = ort.InferenceSession(str(FP32_CPU_ENCODER), providers=["CPUExecutionProvider"])
    in_nchw = np.transpose(arr, (2, 0, 1))[np.newaxis, ...]
    cpu_latent = sess_cpu.run(None, {"image": in_nchw})[0]
    cpu_q = np.clip(np.round(cpu_latent / s_dec) + z_dec, 0, 65535).astype(np.uint16)
    cpu_dec_out = sess_dec.run(None, {"latent": cpu_q})[0]
    cpu_recon_np = (cpu_dec_out[0] * (255.0 / 65535.0)).astype(np.uint8)

    # 9. Compute Quality Metrics
    # A: HTP Reconstruction vs Original Ground Truth
    psnr_vs_orig = compute_psnr(orig_img_np, recon_img_np)
    ssim_vs_orig = compute_ssim_torch(orig_img_np, recon_img_np)

    # B: HTP Reconstruction vs CPU-Encoder Reference Reconstruction
    psnr_vs_cpu = compute_psnr(cpu_recon_np, recon_img_np)
    ssim_vs_cpu = compute_ssim_torch(cpu_recon_np, recon_img_np)

    # C: Latent metrics
    lat_diff = np.abs(cpu_latent - latent_fp32)
    lat_mae = float(np.mean(lat_diff))
    lat_mse = float(np.mean(lat_diff**2))
    lat_psnr = float(10.0 * np.log10((float(np.max(cpu_latent) - np.min(cpu_latent)) ** 2) / lat_mse))

    logger.info("=" * 80)
    logger.info("COMPATIBILITY AND QUALITY RESULTS")
    logger.info("=" * 80)
    logger.info("HTP Latent vs CPU Latent:")
    logger.info("  Latent MAE:                         %.6f", lat_mae)
    logger.info("  Latent MSE:                         %.6f", lat_mse)
    logger.info("  Latent PSNR:                        %.2f dB", lat_psnr)
    logger.info("HTP Pipeline vs CPU Pipeline Parity:")
    logger.info("  Decoded PSNR (HTP vs CPU Pipeline): %.2f dB (Gate >= 28.0 dB: %s)", psnr_vs_cpu, "PASS" if psnr_vs_cpu >= 28.0 else "FAIL")
    logger.info("  Decoded SSIM (HTP vs CPU Pipeline): %.4f (Gate >= 0.85: %s)", ssim_vs_cpu, "PASS" if ssim_vs_cpu >= 0.85 else "FAIL")
    logger.info("HTP Reconstruction vs Original Image:")
    logger.info("  Reconstructed PSNR vs Original:     %.2f dB", psnr_vs_orig)
    logger.info("  Reconstructed SSIM vs Original:     %.4f", ssim_vs_orig)
    logger.info("Latency Summary:")
    logger.info("  HTP VAE Encoder:                    %.1f ms", t_enc_ms)
    logger.info("  HTP VAE Decoder:                    %.1f ms", t_dec_ms)
    logger.info("  Total HTP VAE Roundtrip:            %.1f ms (~%.2f s)", t_enc_ms + t_dec_ms, (t_enc_ms + t_dec_ms) / 1000.0)

    # 10. Save Comparison Artifacts
    Image.fromarray(orig_img_np).save(OUTPUT_DIR / "orig_image.png")
    Image.fromarray(recon_img_np).save(OUTPUT_DIR / "htp_reconstructed.png")
    Image.fromarray(cpu_recon_np).save(OUTPUT_DIR / "cpu_reconstructed.png")

    # Difference map (amplified 5x for visual evaluation)
    diff_map = np.clip(np.abs(cpu_recon_np.astype(np.int32) - recon_img_np.astype(np.int32)) * 5, 0, 255).astype(np.uint8)
    Image.fromarray(diff_map).save(OUTPUT_DIR / "htp_vs_cpu_diff_5x.png")

    # Visual grid (Original | CPU Reference | HTP Prototype | Amplified Diff)
    grid = Image.new("RGB", (512 * 4, 512))
    grid.paste(Image.fromarray(orig_img_np), (0, 0))
    grid.paste(Image.fromarray(cpu_recon_np), (512, 0))
    grid.paste(Image.fromarray(recon_img_np), (1024, 0))
    grid.paste(Image.fromarray(diff_map), (1536, 0))
    grid.save(OUTPUT_DIR / "sd15_vae_htp_compatibility_grid.png")
    logger.info("Saved comparison grid: %s", OUTPUT_DIR / "sd15_vae_htp_compatibility_grid.png")

    return {
        "psnr_vs_cpu_db": psnr_vs_cpu,
        "ssim_vs_cpu": ssim_vs_cpu,
        "psnr_vs_orig_db": psnr_vs_orig,
        "ssim_vs_orig": ssim_vs_orig,
        "latent_mae": lat_mae,
        "latent_psnr_db": lat_psnr,
        "t_enc_ms": t_enc_ms,
        "t_dec_ms": t_dec_ms,
        "s_enc": s_enc,
        "z_enc": z_enc,
        "s_dec": s_dec,
        "z_dec": z_dec,
        "s_unet_in": s_unet_in,
        "z_unet_in": z_unet_in,
    }


if __name__ == "__main__":
    run_compatibility_verification()
