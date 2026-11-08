"""
Qualcomm Hexagon HTP SD1.5 Inpainting Adapter for HK NPU STUDIO.
Integrates Qualcomm Hexagon HTP VAE-Encoder with Qualcomm Hexagon HTP UNet & VAE-Decoder via Latent Blending.
All pipeline stages (Encoder, CLIP, UNet, Decoder) execute purely on Qualcomm Hexagon HTP NPU without CPU fallback.
"""

from __future__ import annotations

import html
import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PIL import Image, ImageFilter

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

logger = logging.getLogger(__name__)

# Default model search paths
DEFAULT_LOCALAPPDATA_MODEL_DIR = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "HK NPU STUDIO" / "models" / "stable_diffusion_v1_5_qnn"
)
DEFAULT_REPO_MODEL_DIR = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn"

# Quantization Parameters for Qualcomm Hexagon HTP SD1.5 Pipeline
# 1. HTP VAE-Encoder Input (UINT16, NHWC [1, 512, 512, 3], symmetric [-1, 1])
VAE_ENCODER_IN_SCALE: float = 0.000030518044
VAE_ENCODER_IN_ZERO_POINT: int = 32768

# 2. HTP VAE-Encoder Output (UINT16, NHWC [1, 64, 64, 4])
VAE_ENCODER_OUT_SCALE: float = 0.00012290581
VAE_ENCODER_OUT_ZERO_POINT: int = 35417

# 3. HTP UNet Latent Input (UINT16, NHWC [1, 64, 64, 4])
UNET_LATENT_IN_SCALE: float = 0.00024176308943424374
UNET_LATENT_IN_ZERO_POINT: int = 33983

# 4. HTP UNet Timestep Input (UINT16, [1, 1])
UNET_TIMESTEP_IN_SCALE: float = 0.014770733192563057
UNET_TIMESTEP_IN_ZERO_POINT: int = 0

# 5. HTP UNet Text Embedding Input (UINT16, [1, 77, 768])
UNET_TEXT_IN_SCALE: float = 0.0009331560577265918
UNET_TEXT_IN_ZERO_POINT: int = 30103

# 6. HTP UNet Latent Output (UINT16, NHWC [1, 64, 64, 4])
UNET_LATENT_OUT_SCALE: float = 0.0001881735515780747
UNET_LATENT_OUT_ZERO_POINT: int = 32340

# 7. HTP VAE-Decoder Latent Input (UINT16, NHWC [1, 64, 64, 4])
VAE_DECODER_IN_SCALE: float = 0.00034003707696683705
VAE_DECODER_IN_ZERO_POINT: int = 34382

# 8. HTP VAE-Decoder Image Output (UINT16, NHWC [1, 512, 512, 3])
VAE_DECODER_OUT_SCALE: float = 1.5259021893143654e-05
VAE_DECODER_OUT_ZERO_POINT: int = 0

# 9. HTP CLIP Text-Encoder Output (UINT16, [1, 77, 768])
CLIP_TEXT_OUT_SCALE: float = 0.0009303585393354297
CLIP_TEXT_OUT_ZERO_POINT: int = 30063


def quantize_encoder_input(img_rgb_nhwc_float: np.ndarray) -> np.ndarray:
    """
    Quantize normalized NHWC [-1.0, 1.0] image to uint16 for HTP VAE-Encoder.
    Formula: clip(round(x / scale) + zero_point, 0, 65535).astype(uint16)
    """
    return np.clip(
        np.round(img_rgb_nhwc_float / VAE_ENCODER_IN_SCALE) + VAE_ENCODER_IN_ZERO_POINT,
        0,
        65535,
    ).astype(np.uint16)


def dequantize_encoder_output(latent_uint16: np.ndarray) -> np.ndarray:
    """
    Dequantize uint16 HTP VAE-Encoder output to FP32 latent space.
    Formula: (uint16 - zero_point) * scale
    """
    return (latent_uint16.astype(np.float32) - VAE_ENCODER_OUT_ZERO_POINT) * VAE_ENCODER_OUT_SCALE


def quantize_unet_latent(latent_fp32: np.ndarray) -> np.ndarray:
    """
    Quantize FP32 latent to uint16 for HTP UNet latent input.
    Formula: clip(round(latent / scale) + zero_point, 0, 65535).astype(uint16)
    """
    return np.clip(
        np.round(latent_fp32 / UNET_LATENT_IN_SCALE) + UNET_LATENT_IN_ZERO_POINT,
        0,
        65535,
    ).astype(np.uint16)


def quantize_decoder_latent(latent_fp32: np.ndarray) -> np.ndarray:
    """
    Quantize FP32 latent to uint16 for HTP VAE-Decoder latent input.
    Formula: clip(round(latent / scale) + zero_point, 0, 65535).astype(uint16)
    """
    return np.clip(
        np.round(latent_fp32 / VAE_DECODER_IN_SCALE) + VAE_DECODER_IN_ZERO_POINT,
        0,
        65535,
    ).astype(np.uint16)


def generate_feathered_mask(
    mask: Image.Image,
    dilate_pixels: int = 0,
    feather_radius: int = 5,
) -> Image.Image:
    """
    Produce a feathered alpha composite mask with controlled dilation and Gaussian smoothing.
    Supports both binary masks and soft continuous grayscale brush masks.

    Guarantees:
    - If dilate_pixels == 0, every pixel outside the original mask (mask == 0) remains
      strictly 0 (alpha = 0.0), guaranteeing 100% bit-exact preservation of original pixels.
    - If dilate_pixels > 0, the edit zone is expanded by dilate_pixels before smoothing,
      and every pixel outside the dilated zone remains strictly 0.
    - Inside the edit zone, alpha smoothly blends according to brush softness and feathering,
      eliminating hard 1-pixel edges, seams, and VAE transition steps.
    """
    if mask.mode != "L":
        mask = mask.convert("L")

    m_arr = np.array(mask, dtype=np.uint8)

    # If mask is entirely empty or entirely full, return early
    if not np.any(m_arr) or np.all(m_arr == 255):
        return mask.copy()

    # Determine whether mask is binary (only 0 and 255) or continuous grayscale (soft brush)
    unique_vals = np.unique(m_arr)
    is_pure_binary = len(unique_vals) <= 2 and (unique_vals[0] == 0) and (len(unique_vals) == 1 or unique_vals[1] == 255)

    # Active zone: any non-zero pixel in mask
    active_binary = (m_arr > 0).astype(np.uint8) * 255
    active_zone_img = Image.fromarray(active_binary, mode="L")

    if dilate_pixels > 0:
        k_size = 2 * int(dilate_pixels) + 1
        zone_img = active_zone_img.filter(ImageFilter.MaxFilter(k_size))
        zone_arr = np.array(zone_img, dtype=np.uint8)
        dilated_mask_img = mask.filter(ImageFilter.MaxFilter(k_size))
    else:
        zone_img = active_zone_img
        zone_arr = active_binary
        dilated_mask_img = mask

    if feather_radius <= 0:
        if is_pure_binary:
            return zone_img
        else:
            res_arr = np.array(dilated_mask_img, dtype=np.uint8)
            res_arr[zone_arr == 0] = 0
            return Image.fromarray(res_arr, mode="L")

    # When feather_radius > 0:
    if is_pure_binary:
        blur_img = zone_img.filter(ImageFilter.GaussianBlur(radius=float(feather_radius)))
        blur_arr = np.array(blur_img, dtype=np.float32)
        max_b = float(np.max(blur_arr[zone_arr > 0])) if np.any(zone_arr > 0) else 255.0
        denom = max(1.0, max_b - 127.5)
        alpha = np.clip((blur_arr - 127.5) / denom, 0.0, 1.0)
        alpha[zone_arr == 0] = 0.0
        alpha_uint8 = np.round(alpha * 255.0).astype(np.uint8)
        return Image.fromarray(alpha_uint8, mode="L")
    else:
        blur_img = dilated_mask_img.filter(ImageFilter.GaussianBlur(radius=float(feather_radius)))
        blur_arr = np.array(blur_img, dtype=np.float32)
        # Normalize by maximum inside active zone to preserve core opacity without ghosting
        max_b = float(np.max(blur_arr[zone_arr > 0])) if np.any(zone_arr > 0) else 255.0
        denom = max(1.0, max_b)
        alpha = np.clip(blur_arr / denom, 0.0, 1.0)
        alpha[zone_arr == 0] = 0.0
        alpha_uint8 = np.round(alpha * 255.0).astype(np.uint8)
        return Image.fromarray(alpha_uint8, mode="L")


def rgb2lab_np(rgb: np.ndarray) -> np.ndarray:
    """
    Convert RGB float array [0.0, 1.0] in sRGB to CIE L*a*b*.
    Input shape: (..., 3) with values in [0.0, 1.0].
    """
    # Linearize sRGB
    mask = rgb > 0.04045
    linear = np.empty_like(rgb)
    linear[mask] = ((rgb[mask] + 0.055) / 1.055) ** 2.4
    linear[~mask] = rgb[~mask] / 12.92

    # sRGB to XYZ (D65 illuminant matrix)
    mat = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ], dtype=np.float32)
    xyz = np.tensordot(linear, mat.T, axes=([linear.ndim - 1], [1]))

    # Reference white D65
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    x = xyz[..., 0] / Xn
    y = xyz[..., 1] / Yn
    z = xyz[..., 2] / Zn

    epsilon = 0.008856  # (6/29)^3
    kappa = 903.3       # (29/3)^3

    fx = np.where(x > epsilon, np.cbrt(x), (kappa * x + 16.0) / 116.0)
    fy = np.where(y > epsilon, np.cbrt(y), (kappa * y + 16.0) / 116.0)
    fz = np.where(z > epsilon, np.cbrt(z), (kappa * z + 16.0) / 116.0)

    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)

    return np.stack([L, a, b], axis=-1)


def lab2rgb_np(lab: np.ndarray) -> np.ndarray:
    """
    Convert CIE L*a*b* array to sRGB float array [0.0, 1.0].
    Input shape: (..., 3) where L in [0, 100], a, b in [-128, 127].
    """
    L = lab[..., 0]
    a = lab[..., 1]
    b = lab[..., 2]

    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    epsilon = 0.008856
    kappa = 903.3

    x = np.where(fx**3 > epsilon, fx**3, (116.0 * fx - 16.0) / kappa)
    y = np.where(L > kappa * epsilon, ((L + 16.0) / 116.0) ** 3, L / kappa)
    z = np.where(fz**3 > epsilon, fz**3, (116.0 * fz - 16.0) / kappa)

    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    xyz = np.stack([x * Xn, y * Yn, z * Zn], axis=-1)

    # XYZ to linear sRGB
    mat_inv = np.array([
        [ 3.2404542, -1.5371385, -0.4985314],
        [-0.9692660,  1.8760108,  0.0415560],
        [ 0.0556434, -0.2040259,  1.0572252],
    ], dtype=np.float32)
    linear = np.clip(np.tensordot(xyz, mat_inv.T, axes=([xyz.ndim - 1], [1])), 0.0, 1.0)

    # Gamma compression to sRGB
    mask = linear > 0.0031308
    srgb = np.empty_like(linear)
    srgb[mask] = 1.055 * (linear[mask] ** (1.0 / 2.4)) - 0.055
    srgb[~mask] = 12.92 * linear[~mask]

    return np.clip(srgb, 0.0, 1.0)


def align_color_lab(
    source_img: Image.Image,
    generated_img: Image.Image,
    mask_img: Image.Image,
    dilate_pixels: int = 0,
    feather_radius: int = 5,
) -> Image.Image:
    """
    Harmonize luminance and color tint of generated inpainting patch to match surrounding source.
    Measures delta L*, a*, b* in a boundary ring around the edit area, clamped defensively.
    """
    if mask_img.mode != "L":
        mask_img = mask_img.convert("L")
    m_arr = np.array(mask_img, dtype=np.uint8)
    active_mask = (m_arr > 0).astype(np.uint8) * 255
    if not np.any(active_mask) or np.all(active_mask):
        return generated_img

    base_mask_img = Image.fromarray(active_mask, mode="L")
    if dilate_pixels > 0:
        zone_img = base_mask_img.filter(ImageFilter.MaxFilter(2 * int(dilate_pixels) + 1))
        zone_arr = np.array(zone_img, dtype=np.uint8)
    else:
        zone_img = base_mask_img
        zone_arr = active_mask

    # Define boundary ring around the edit zone
    ring_radius = max(6, int(feather_radius) + 2)
    outer_zone_img = zone_img.filter(ImageFilter.MaxFilter(2 * ring_radius + 1))
    outer_arr = np.array(outer_zone_img, dtype=np.uint8)
    ring_mask = (outer_arr > 0) & (zone_arr == 0)

    if np.sum(ring_mask) < 30:
        return generated_img

    src_rgb = np.array(source_img.convert("RGB"), dtype=np.float32) / 255.0
    gen_rgb = np.array(generated_img.convert("RGB"), dtype=np.float32) / 255.0

    src_lab = rgb2lab_np(src_rgb)
    gen_lab = rgb2lab_np(gen_rgb)

    delta_L = float(np.mean(src_lab[ring_mask, 0]) - np.mean(gen_lab[ring_mask, 0]))
    delta_a = float(np.mean(src_lab[ring_mask, 1]) - np.mean(gen_lab[ring_mask, 1]))
    delta_b = float(np.mean(src_lab[ring_mask, 2]) - np.mean(gen_lab[ring_mask, 2]))

    # Defensively clamp adjustments to prevent unnatural shifts
    delta_L = float(np.clip(delta_L, -8.0, 8.0))
    delta_a = float(np.clip(delta_a, -4.0, 4.0))
    delta_b = float(np.clip(delta_b, -4.0, 4.0))

    adj_lab = gen_lab.copy()
    adj_lab[..., 0] = np.clip(adj_lab[..., 0] + delta_L, 0.0, 100.0)
    adj_lab[..., 1] = np.clip(adj_lab[..., 1] + delta_a, -128.0, 127.0)
    adj_lab[..., 2] = np.clip(adj_lab[..., 2] + delta_b, -128.0, 127.0)

    aligned_rgb = lab2rgb_np(adj_lab)
    aligned_uint8 = np.round(aligned_rgb * 255.0).astype(np.uint8)
    return Image.fromarray(aligned_uint8, mode="RGB")


def _configure_qnn_runtime_path() -> None:
    """Ensure onnxruntime_qnn library directory is present on PATH and DLL search."""
    try:
        spec = importlib.util.find_spec("onnxruntime_qnn")
        if spec is None or spec.origin is None:
            return
        qnn_dir = Path(spec.origin).resolve().parent
        os.environ["PATH"] = str(qnn_dir) + os.pathsep + os.environ.get("PATH", "")
        os.environ["ADSP_LIBRARY_PATH"] = str(qnn_dir)
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(str(qnn_dir))
            except OSError:
                pass
    except Exception:
        logger.exception("QNN-Laufzeitpfad konnte nicht vorbereitet werden.")


_configure_qnn_runtime_path()


def _resolve_worker_python() -> str:
    """Prefer configured QNN Python or fallback to current interpreter."""
    configured = os.environ.get("SNAPDRAGON_QNN_PYTHON", "").strip()
    candidates = [
        Path(configured) if configured else None,
        Path(sys.executable),
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file():
            return str(candidate)
    raise FileNotFoundError("Kein verwendbarer Python-Interpreter für den QNN-Worker gefunden.")


def bytes_to_unicode() -> dict[int, str]:
    bs = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("¡"), ord("¬") + 1))
        + list(range(ord("®"), ord("ÿ") + 1))
    )
    cs = bs[:]
    n = 0
    for b in range(2**8):
        if b not in bs:
            bs.append(b)
            cs.append(2**8 + n)
            n += 1
    cs = [chr(n) for n in cs]
    return dict(zip(bs, cs))


class SimpleCLIPTokenizer:
    """Pure-Python CLIP Tokenizer for SD1.5 prompt embeddings."""

    def __init__(self, vocab_path: str | Path, merges_path: str | Path) -> None:
        with open(vocab_path, "r", encoding="utf-8") as f:
            self.encoder = json.load(f)
        self.decoder = {v: k for k, v in self.encoder.items()}
        self.byte_encoder = bytes_to_unicode()
        self.pat = re.compile(
            r"""<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|[^\W\d_]+|\d+|(?:[^\s\w]|_)+""",
            re.IGNORECASE,
        )
        with open(merges_path, "r", encoding="utf-8") as f:
            merges = f.read().split("\n")
        bpe_merges = []
        for line in merges:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            bpe_merges.append(tuple(line.split()))
        self.bpe_ranks = dict(zip(bpe_merges, range(len(bpe_merges))))
        self.cache: dict[str, str] = {}

    def get_pairs(self, word: tuple[str, ...]) -> set[tuple[str, str]]:
        pairs = set()
        prev_char = word[0]
        for char in word[1:]:
            pairs.add((prev_char, char))
            prev_char = char
        return pairs

    def bpe(self, token: str) -> str:
        if token in self.cache:
            return self.cache[token]
        word = tuple(token[:-1]) + (token[-1] + "</w>",)
        pairs = self.get_pairs(word)
        if not pairs:
            return token + "</w>"
        while True:
            bigram = min(pairs, key=lambda pair: self.bpe_ranks.get(pair, float("inf")))
            if bigram not in self.bpe_ranks:
                break
            first, second = bigram
            new_word = []
            i = 0
            while i < len(word):
                try:
                    j = word.index(first, i)
                    new_word.extend(word[i:j])
                    i = j
                except ValueError:
                    new_word.extend(word[i:])
                    break
                if word[i] == first and i < len(word) - 1 and word[i + 1] == second:
                    new_word.append(first + second)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            word = tuple(new_word)
            if len(word) == 1:
                break
            else:
                pairs = self.get_pairs(word)
        word = " ".join(word)
        self.cache[token] = word
        return word

    def encode(self, text: str) -> list[int]:
        bpe_tokens = []
        text = html.unescape(html.unescape(text))
        text = re.sub(r"\s+", " ", text.lower()).strip()
        for token in re.findall(self.pat, text):
            token = "".join(self.byte_encoder[b] for b in token.encode("utf-8"))
            bpe_tokens.extend(self.bpe(token).split(" "))
        return [self.encoder[bpe_token] for bpe_token in bpe_tokens]

    def tokenize_prompt(self, prompt: str, max_length: int = 77) -> list[int]:
        eos_token_id = 49407
        ids = [49406] + self.encode(prompt) + [49407]
        if len(ids) < max_length:
            ids = ids + [eos_token_id] * (max_length - len(ids))
        else:
            ids = ids[:max_length]
            ids[-1] = eos_token_id
        return ids


class EulerScheduler:
    """Euler Discrete Scheduler for Stable Diffusion 1.5."""

    def __init__(self, num_train_timesteps: int = 1000, beta_start: float = 0.00085, beta_end: float = 0.012) -> None:
        self.num_train_timesteps = num_train_timesteps
        self.betas = np.linspace(beta_start**0.5, beta_end**0.5, num_train_timesteps, dtype=np.float32) ** 2
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = np.cumprod(self.alphas, axis=0)
        self.timesteps: np.ndarray = np.array([], dtype=np.int32)
        self.sigmas: np.ndarray = np.array([], dtype=np.float32)

    def set_timesteps(self, num_inference_steps: int) -> None:
        step_ratio = self.num_train_timesteps // num_inference_steps
        self.timesteps = (
            np.arange(num_inference_steps) * step_ratio
        ).round()[::-1].astype(np.int32) + 1

        sigmas_full = ((1.0 - self.alphas_cumprod) / self.alphas_cumprod) ** 0.5
        sigmas = []
        for t in self.timesteps:
            sigmas.append(sigmas_full[t])
        sigmas.append(0.0)
        self.sigmas = np.array(sigmas, dtype=np.float32)


@dataclass
class SD15QnnInpaintingResult:
    """Execution result from SD1.5 QNN Inpainting Adapter."""

    success: bool
    output: np.ndarray | None = None
    output_path: str | Path | None = None
    error_code: str | None = None
    error_message: str | None = None
    backend_name: str = "sd15_qnn_htp"
    metadata: dict[str, Any] = field(default_factory=dict)


class SD15QnnInpaintingAdapter:
    """
    Subprocess-isolated or in-process adapter running SD1.5 inpainting with:
    - 1x Qualcomm Hexagon HTP VAE-Encoder (initial latent z0, pure HTP EPContext, no CPU fallback)
    - 20x UNet on Qualcomm Hexagon HTP (Latent Blending via EulerScheduler)
    - 1x VAE-Decoder on Qualcomm Hexagon HTP
    - Pixel-perfect alpha composite outside mask
    """

    def __init__(
        self,
        model_dir: Path | None = None,
        encoder_path: Path | None = None,
    ) -> None:
        self.model_dir = model_dir or self._find_qnn_model_dir()
        self.encoder_path = encoder_path or self._find_encoder_path()
        self._active_process: subprocess.Popen | None = None
        self._cancel_lock = threading.Lock()
        self._is_cancelled: bool = False

    @classmethod
    def _find_qnn_model_dir(cls) -> Path:
        for candidate in [DEFAULT_LOCALAPPDATA_MODEL_DIR, DEFAULT_REPO_MODEL_DIR]:
            if (candidate / "unet.onnx").is_file() and (candidate / "vae.onnx").is_file():
                return candidate
        return DEFAULT_LOCALAPPDATA_MODEL_DIR

    @classmethod
    def _find_controlnet_dir(cls) -> Path:
        for candidate in [
            DEFAULT_LOCALAPPDATA_MODEL_DIR.parent / "controlnet_canny_qnn",
            DEFAULT_REPO_MODEL_DIR.parent / "controlnet_canny_qnn",
            REPO_ROOT / "models" / "controlnet_canny_qnn",
        ]:
            if (candidate / "controlnet.onnx").is_file() and (candidate / "unet.onnx").is_file():
                return candidate
        return REPO_ROOT / "models" / "controlnet_canny_qnn" 

    @classmethod
    def _find_encoder_path(cls) -> Path:
        for candidate in [
            DEFAULT_REPO_MODEL_DIR / "prototype" / "vae_encoder_htp.onnx",
            DEFAULT_LOCALAPPDATA_MODEL_DIR / "prototype" / "vae_encoder_htp.onnx",
            DEFAULT_LOCALAPPDATA_MODEL_DIR / "vae_encoder_htp.onnx",
            DEFAULT_REPO_MODEL_DIR / "vae_encoder_htp.onnx",
            DEFAULT_REPO_MODEL_DIR / "vae_encoder.onnx",
            DEFAULT_LOCALAPPDATA_MODEL_DIR / "vae_encoder.onnx",
        ]:
            if candidate.is_file():
                return candidate
        return DEFAULT_REPO_MODEL_DIR / "prototype" / "vae_encoder_htp.onnx"

    def cancel(self) -> None:
        """Cancel active worker subprocess if running."""
        with self._cancel_lock:
            self._is_cancelled = True
            process = self._active_process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            except OSError:
                pass
        with self._cancel_lock:
            if self._active_process is process:
                self._active_process = None

    def run(
        self,
        input_image_path: str | Path,
        mask_image_path: str | Path | None = None,
        prompt: str = "",
        output_path: str | Path = "",
        negative_prompt: str = "",
        steps: int = 20,
        seed: int = 42,
        cfg_scale: float = 7.5,
        denoising_strength: float = 1.0,
        feather_radius: int = 5,
        dilate_pixels: int = 0,
        mode: str = "inpaint",
        enable_reference_control: bool = False,
        reference_mode: str = "canny_qnn",
        reference_fidelity: float = 0.75,
        reference_image_path: str | Path | None = None,
        progress_callback: Callable[[str, float, str | None], None] | None = None,
        use_subprocess: bool = True,
    ) -> SD15QnnInpaintingResult:
        """
        Execute inpainting or image-to-image pipeline. Default isolates QAIRT in worker subprocess.
        """
        with self._cancel_lock:
            self._is_cancelled = False
            self._active_process = None

        input_p = Path(input_image_path).resolve()
        output_p = Path(output_path).resolve()

        if not input_p.is_file():
            return SD15QnnInpaintingResult(
                success=False,
                error_code="ERR_INPUT_NOT_FOUND",
                error_message=f"Eingabebild nicht gefunden: {input_p}",
            )

        if mode != "img2img":
            if mask_image_path is None:
                return SD15QnnInpaintingResult(
                    success=False,
                    error_code="ERR_MASK_NOT_FOUND",
                    error_message="Maskenbild ist im Inpainting-Modus erforderlich.",
                )
            mask_p = Path(mask_image_path).resolve()
            if not mask_p.is_file():
                return SD15QnnInpaintingResult(
                    success=False,
                    error_code="ERR_MASK_NOT_FOUND",
                    error_message=f"Maskenbild nicht gefunden: {mask_p}",
                )
            mask_str = str(mask_p)
        else:
            mask_str = ""

        job_data = {
            "mode": mode,
            "input_image_path": str(input_p),
            "mask_image_path": mask_str,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "output_path": str(output_p),
            "steps": int(steps),
            "seed": int(seed),
            "cfg_scale": float(cfg_scale),
            "denoising_strength": float(denoising_strength),
            "feather_radius": int(feather_radius),
            "dilate_pixels": int(dilate_pixels),
            "enable_reference_control": bool(enable_reference_control),
            "reference_mode": str(reference_mode),
            "reference_fidelity": float(reference_fidelity),
            "reference_image_path": str(Path(reference_image_path).resolve()) if reference_image_path else "",
            "encoder_path": str(self.encoder_path.resolve()),
            "model_dir": str(self.model_dir.resolve()),
        }

        if not use_subprocess:
            return self._execute_in_process(job_data, progress_callback=progress_callback)

        return self._execute_in_subprocess(job_data, progress_callback=progress_callback)

    def run_img2img(
        self,
        input_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        negative_prompt: str = "",
        steps: int = 20,
        seed: int = 42,
        cfg_scale: float = 7.5,
        denoising_strength: float = 0.65,
        enable_reference_control: bool = False,
        reference_mode: str = "canny_qnn",
        reference_fidelity: float = 0.75,
        reference_image_path: str | Path | None = None,
        progress_callback: Callable[[str, float, str | None], None] | None = None,
        use_subprocess: bool = True,
    ) -> SD15QnnInpaintingResult:
        """
        Convenience execution of SD1.5 Image-to-Image on Qualcomm Hexagon HTP without mask.
        Supports optional Reference Image Control (Modus A: Canny QNN, Modus B: Decaying Latent Anchor).
        """
        return self.run(
            input_image_path=input_image_path,
            mask_image_path=None,
            prompt=prompt,
            output_path=output_path,
            negative_prompt=negative_prompt,
            steps=steps,
            seed=seed,
            cfg_scale=cfg_scale,
            denoising_strength=denoising_strength,
            mode="img2img",
            enable_reference_control=enable_reference_control,
            reference_mode=reference_mode,
            reference_fidelity=reference_fidelity,
            reference_image_path=reference_image_path,
            progress_callback=progress_callback,
            use_subprocess=use_subprocess,
        )

    def _execute_in_subprocess(
        self,
        job_data: dict[str, Any],
        progress_callback: Callable[[str, float, str | None], None] | None = None,
    ) -> SD15QnnInpaintingResult:
        """Spawn dedicated python worker process to isolate QAIRT runtime."""
        import tempfile

        with self._cancel_lock:
            if self._is_cancelled:
                return SD15QnnInpaintingResult(
                    success=False,
                    error_code="ERR_INPAINTING_CANCELLED",
                    error_message="Inpainting-Vorgang wurde durch den Benutzer abgebrochen.",
                )

        temp_dir = REPO_ROOT / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="qnn_inpaint_", dir=temp_dir) as work_dir:
            work_path = Path(work_dir)
            input_json = work_path / "job_input.json"
            output_json = work_path / "job_output.json"

            with open(input_json, "w", encoding="utf-8") as f:
                json.dump(job_data, f, indent=2)

            python_exe = _resolve_worker_python()
            script_path = Path(__file__).resolve()
            cmd = [python_exe, str(script_path), str(input_json), str(output_json)]

            env = os.environ.copy()
            env["PYTHONPATH"] = os.pathsep.join(
                part for part in (str(REPO_ROOT), env.get("PYTHONPATH", "")) if part
            )

            if progress_callback:
                progress_callback("prepare", 0.05, "QNN Inpainting Worker wird gestartet...")

            with self._cancel_lock:
                if self._is_cancelled:
                    return SD15QnnInpaintingResult(
                        success=False,
                        error_code="ERR_INPAINTING_CANCELLED",
                        error_message="Inpainting-Vorgang wurde durch den Benutzer abgebrochen.",
                    )
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=str(REPO_ROOT),
                    env=env,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                self._active_process = process

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line_str = line.strip()
                    logger.info("[QNN Inpaint Worker] %s", line_str)
                    if progress_callback and line_str.startswith("PROGRESS:"):
                        # Format: PROGRESS:<phase>:<fraction>:<detail>
                        parts = line_str.split(":", 3)
                        if len(parts) >= 4:
                            try:
                                phase = parts[1]
                                frac = float(parts[2])
                                detail = parts[3]
                                progress_callback(phase, frac, detail)
                            except ValueError:
                                pass

            process.wait()
            if process.stdout:
                process.stdout.close()

            with self._cancel_lock:
                was_cancelled = self._is_cancelled
                self._active_process = None

            if was_cancelled:
                return SD15QnnInpaintingResult(
                    success=False,
                    error_code="ERR_INPAINTING_CANCELLED",
                    error_message="Inpainting-Vorgang wurde durch den Benutzer abgebrochen.",
                )

            if not output_json.is_file():
                return SD15QnnInpaintingResult(
                    success=False,
                    error_code="ERR_WORKER_CRASH",
                    error_message=f"QNN Inpainting Worker beendete mit Exit-Code {process.returncode} ohne Ausgabedatei.",
                )

            try:
                with open(output_json, "r", encoding="utf-8") as f:
                    result_dict = json.load(f)
            except Exception as err:
                return SD15QnnInpaintingResult(
                    success=False,
                    error_code="ERR_WORKER_CRASH",
                    error_message=f"QNN Inpainting Worker-Ausgabedatei konnte nicht gelesen werden: {err}",
                )

            return SD15QnnInpaintingResult(
                success=result_dict.get("success", False),
                output_path=result_dict.get("output_path"),
                error_code=result_dict.get("error_code"),
                error_message=result_dict.get("error_message"),
                backend_name=result_dict.get("backend_name", "sd15_qnn_htp"),
                metadata=result_dict.get("metadata", {}),
            )

    @classmethod
    def _execute_in_process(
        cls,
        job_data: dict[str, Any],
        progress_callback: Callable[[str, float, str | None], None] | None = None,
    ) -> SD15QnnInpaintingResult:
        """Physical in-process execution of VAE encode -> QNN UNet inpaint -> VAE decode -> composite."""
        import onnxruntime as ort
        import onnxruntime_qnn as qnn

        input_image_path = Path(job_data["input_image_path"])
        mask_image_path = Path(job_data["mask_image_path"])
        output_path = Path(job_data["output_path"])
        prompt = job_data.get("prompt", "")
        negative_prompt = job_data.get("negative_prompt", "")
        steps = int(job_data.get("steps", 20))
        seed = int(job_data.get("seed", 42))
        cfg_scale = float(job_data.get("cfg_scale", 7.5))
        denoising_strength = max(0.1, min(1.0, float(job_data.get("denoising_strength", 1.0))))
        feather_radius = int(job_data.get("feather_radius", 5))
        dilate_pixels = int(job_data.get("dilate_pixels", 0))
        encoder_path = Path(job_data["encoder_path"])
        model_dir = Path(job_data["model_dir"])
        mode = job_data.get("mode", "inpaint")
        enable_reference_control = bool(job_data.get("enable_reference_control", False))
        reference_mode = str(job_data.get("reference_mode", "canny_qnn"))
        reference_fidelity = max(0.0, min(1.5, float(job_data.get("reference_fidelity", 0.75))))
        ref_img_path_str = job_data.get("reference_image_path", "")
        if ref_img_path_str and Path(ref_img_path_str).is_file():
            reference_image_path = Path(ref_img_path_str)
        else:
            reference_image_path = input_image_path

        is_ref_control = (mode == "img2img" and enable_reference_control)
        is_canny_qnn = (is_ref_control and reference_mode == "canny_qnn")
        is_latent_anchor = (is_ref_control and reference_mode == "latent_anchor")

        def report(phase: str, frac: float, detail: str) -> None:
            # Emit structured stdout for subprocess wrapper and invoke callback
            print(f"PROGRESS:{phase}:{frac:.4f}:{detail}", flush=True)
            if progress_callback:
                progress_callback(phase, frac, detail)

        # 1. Load source image and mask
        report("prepare", 0.05, "Eingabebild und Maske laden...")
        with Image.open(input_image_path) as opened:
            source_img = opened.convert("RGB")
        if source_img.size != (512, 512):
            source_img = source_img.resize((512, 512), Image.Resampling.LANCZOS)
        source_np = np.array(source_img, dtype=np.uint8)

        if mode != "img2img":
            with Image.open(mask_image_path) as opened:
                mask_img = opened.convert("L")
            if mask_img.size != (512, 512):
                mask_img = mask_img.resize((512, 512), Image.Resampling.BILINEAR)
            mask_np = np.array(mask_img, dtype=np.uint8)

            # 2. Downsample mask to 64x64 latent resolution
            # Polarität: 255 (Weiß) = Inpaint/Modifizieren, 0 (Schwarz) = Original beibehalten
            mask_64_img = mask_img.resize((64, 64), Image.Resampling.BILINEAR)
            mask_64_np = np.array(mask_64_img, dtype=np.float32) / 255.0
            # Ensure full unit variance in latent space without boundary attenuation
            mask_latent = (mask_64_np >= 0.5).astype(np.float32)[np.newaxis, :, :, np.newaxis]
            # Shape: [1, 64, 64, 1]
        else:
            mask_img = None
            mask_np = None
            mask_latent = None

        # 3. Setup Qualcomm Hexagon HTP Sessions
        report("setup_htp", 0.10, "Qualcomm Hexagon HTP Sessions initialisieren...")
        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
        all_devices = ort.get_ep_devices()
        selected_devices = [d for d in all_devices if d.ep_name == "QNNExecutionProvider"]
        if not selected_devices:
            raise RuntimeError("No QNNExecutionProvider devices found for Hexagon HTP.")

        qnn_opts = ort.SessionOptions()
        qnn_opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        provider_options = {"backend_path": qnn.get_qnn_htp_path()}
        qnn_opts.add_provider_for_devices(selected_devices, provider_options)

        vae_encoder_session = ort.InferenceSession(str(encoder_path), sess_options=qnn_opts)
        text_encoder_session = ort.InferenceSession(str(model_dir / "text_encoder.onnx"), sess_options=qnn_opts)
        vae_session = ort.InferenceSession(str(model_dir / "vae.onnx"), sess_options=qnn_opts)

        controlnet_session = None
        cn_meta = None
        if is_canny_qnn:
            cn_model_dir = cls._find_controlnet_dir()
            with open(cn_model_dir / "metadata.json", "r", encoding="utf-8") as f_meta:
                cn_meta = json.load(f_meta)["model_files"]
            controlnet_session = ort.InferenceSession(str(cn_model_dir / "controlnet.onnx"), sess_options=qnn_opts)
            unet_session = ort.InferenceSession(str(cn_model_dir / "unet.onnx"), sess_options=qnn_opts)
        else:
            unet_session = ort.InferenceSession(str(model_dir / "unet.onnx"), sess_options=qnn_opts)

        # 4. Qualcomm Hexagon HTP VAE Encoding
        report("vae_encode", 0.18, "Originalbild enkodieren (HTP VAE-Encoder)...")
        img_norm = (source_np.astype(np.float32) / 255.0) * 2.0 - 1.0  # [-1.0, 1.0]
        img_nhwc = img_norm[np.newaxis, ...]  # [1, 512, 512, 3]
        img_quant = quantize_encoder_input(img_nhwc)

        enc_in_name = (
            vae_encoder_session.get_inputs()[0].name
            if hasattr(vae_encoder_session, "get_inputs") and vae_encoder_session.get_inputs()
            else "image_q_to_dq"
        )
        enc_out_name = (
            vae_encoder_session.get_outputs()[0].name
            if hasattr(vae_encoder_session, "get_outputs") and vae_encoder_session.get_outputs()
            else "/Mul_1_output_0_QuantizeLinear"
        )

        t_enc_start = time.perf_counter()
        enc_out_q = vae_encoder_session.run([enc_out_name], {enc_in_name: img_quant})[0]
        t_enc_ms = (time.perf_counter() - t_enc_start) * 1000.0

        # Dequantize encoder output to FP32 latent
        z0 = dequantize_encoder_output(enc_out_q)  # [1, 64, 64, 4] float32

        # Setup Reference Image features
        canny_quant = None
        z_ref0 = None
        if is_canny_qnn:
            from engine.controlnet_canny_backend import canny_edge_detector
            canny_edges = canny_edge_detector(str(reference_image_path), low_threshold=15, high_threshold=45)
            canny_edges_f = canny_edges.astype(np.float32) / 255.0
            canny_rgb_batch_f = np.expand_dims(np.stack([canny_edges_f, canny_edges_f, canny_edges_f], axis=-1), axis=0)
            p_cond = cn_meta["controlnet.onnx"]["inputs"]["image_cond"]["quantization_parameters"]
            canny_quant = np.clip(np.round(canny_rgb_batch_f / p_cond["scale"]) + p_cond["zero_point"], 0, 65535).astype(np.uint16)
        elif is_latent_anchor:
            if reference_image_path.resolve() == input_image_path.resolve():
                z_ref0 = z0
            else:
                with Image.open(reference_image_path) as ref_opened:
                    ref_img = ref_opened.convert("RGB")
                if ref_img.size != (512, 512):
                    ref_img = ref_img.resize((512, 512), Image.Resampling.LANCZOS)
                ref_norm = (np.array(ref_img, dtype=np.float32) / 255.0) * 2.0 - 1.0
                ref_quant = quantize_encoder_input(ref_norm[np.newaxis, ...])
                ref_enc_out = vae_encoder_session.run([enc_out_name], {enc_in_name: ref_quant})[0]
                z_ref0 = dequantize_encoder_output(ref_enc_out)

        # 5. Tokenize & Encode Text Prompts
        report("text_encode", 0.25, "Prompt enkodieren (HTP CLIP Text-Encoder)...")
        vocab_path = model_dir / "tokenizer" / "vocab.json"
        merges_path = model_dir / "tokenizer" / "merges.txt"
        tokenizer = SimpleCLIPTokenizer(vocab_path, merges_path)

        cond_tokens = tokenizer.tokenize_prompt(prompt)
        uncond_tokens = tokenizer.tokenize_prompt(negative_prompt)
        cond_arr = np.array([cond_tokens], dtype=np.int32)
        uncond_arr = np.array([uncond_tokens], dtype=np.int32)

        t_text_start = time.perf_counter()
        cond_emb_q = text_encoder_session.run(["text_embedding"], {"tokens": cond_arr})[0]
        uncond_emb_q = text_encoder_session.run(["text_embedding"], {"tokens": uncond_arr})[0]
        t_text_ms = (time.perf_counter() - t_text_start) * 1000.0

        # Dequantize text embeddings
        cond_emb_f = (cond_emb_q.astype(np.float32) - CLIP_TEXT_OUT_ZERO_POINT) * CLIP_TEXT_OUT_SCALE
        uncond_emb_f = (uncond_emb_q.astype(np.float32) - CLIP_TEXT_OUT_ZERO_POINT) * CLIP_TEXT_OUT_SCALE

        # Re-quantize for UNet / ControlNet text_emb input
        if is_canny_qnn:
            p_txt_cn = cn_meta["controlnet.onnx"]["inputs"]["text_emb"]["quantization_parameters"]
            cond_emb_cn = np.clip(np.round(cond_emb_f / p_txt_cn["scale"]) + p_txt_cn["zero_point"], 0, 65535).astype(np.uint16)

            p_txt_u = cn_meta["unet.onnx"]["inputs"]["text_emb"]["quantization_parameters"]
            cond_emb_unet = np.clip(np.round(cond_emb_f / p_txt_u["scale"]) + p_txt_u["zero_point"], 0, 65535).astype(np.uint16)
            uncond_emb_unet = np.clip(np.round(uncond_emb_f / p_txt_u["scale"]) + p_txt_u["zero_point"], 0, 65535).astype(np.uint16)
        else:
            cond_emb_cn = None
            cond_emb_unet = np.clip(
                np.round(cond_emb_f / UNET_TEXT_IN_SCALE) + UNET_TEXT_IN_ZERO_POINT, 0, 65535
            ).astype(np.uint16)
            uncond_emb_unet = np.clip(
                np.round(uncond_emb_f / UNET_TEXT_IN_SCALE) + UNET_TEXT_IN_ZERO_POINT, 0, 65535
            ).astype(np.uint16)

        # 6. Setup Scheduler & Initial Latents
        scheduler = EulerScheduler()
        scheduler.set_timesteps(steps)

        rng = np.random.default_rng(seed=seed)
        noise = rng.standard_normal((1, 64, 64, 4), dtype=np.float32)

        # Timestep mapping for Denoising Strength
        num_inference_steps = max(1, round(steps * denoising_strength))
        t_start = steps - num_inference_steps
        active_timesteps = scheduler.timesteps[t_start:]
        active_sigmas = scheduler.sigmas[t_start:]
        sigma_start = active_sigmas[0]

        # Initialize initial latents with Euler noise scaling
        if mode == "img2img":
            if denoising_strength >= 1.0:
                latents = noise * sigma_start
            else:
                latents = z0 + noise * sigma_start
        else:
            # Masked inpainting
            if denoising_strength >= 1.0:
                init_orig_noisy = z0 + noise * sigma_start
                init_masked_noisy = noise * sigma_start
                latents = mask_latent * init_masked_noisy + (1.0 - mask_latent) * init_orig_noisy
            else:
                latents = z0 + noise * sigma_start

        # 7. Iterative Denoising on Qualcomm Hexagon HTP with Latent Blending
        unet_step_times: list[float] = []
        cn_step_times: list[float] = []

        if is_canny_qnn:
            p_lat_cn = cn_meta["controlnet.onnx"]["inputs"]["latent"]["quantization_parameters"]
            p_t_cn = cn_meta["controlnet.onnx"]["inputs"]["timestep"]["quantization_parameters"]
            p_lat_u = cn_meta["unet.onnx"]["inputs"]["latent"]["quantization_parameters"]
            p_t_u = cn_meta["unet.onnx"]["inputs"]["timestep"]["quantization_parameters"]
            p_out_u = cn_meta["unet.onnx"]["outputs"]["output_latent"]["quantization_parameters"]
            cn_out_names = [o.name for o in controlnet_session.get_outputs()]

        for step_idx, t in enumerate(active_timesteps):
            sigma = active_sigmas[step_idx]
            next_sigma = active_sigmas[step_idx + 1]

            frac = 0.30 + 0.55 * ((step_idx + 1) / num_inference_steps)
            report("denoise", frac, f"Schritt {step_idx + 1}/{num_inference_steps} (HTP NPU)...")

            # Scale latents for UNet input
            latent_model_input = latents / ((sigma**2 + 1.0) ** 0.5)

            if is_canny_qnn:
                # ControlNet forward pass on Hexagon HTP
                lat_q_cn = np.clip(np.round(latent_model_input / p_lat_cn["scale"]) + p_lat_cn["zero_point"], 0, 65535).astype(np.uint16)
                t_q_cn = np.clip(np.round(t / p_t_cn["scale"]) + p_t_cn["zero_point"], 0, 65535).astype(np.uint16)
                t_arr_cn = np.array([[t_q_cn]], dtype=np.uint16)

                t_cn_start = time.perf_counter()
                cn_outs = controlnet_session.run(None, {
                    "latent": lat_q_cn,
                    "timestep": t_arr_cn,
                    "text_emb": cond_emb_cn,
                    "image_cond": canny_quant,
                })
                cn_step_times.append((time.perf_counter() - t_cn_start) * 1000.0)

                # Requantize 13 ControlNet residuals scaled by reference_fidelity
                cn_dict = dict(zip(cn_out_names, cn_outs))
                cn_residuals = {}
                for b_idx in range(12):
                    c_name = f"down_block_{b_idx}"
                    u_name = f"controlnet_downblock{b_idx}"
                    p_c = cn_meta["controlnet.onnx"]["outputs"][c_name]["quantization_parameters"]
                    p_u = cn_meta["unet.onnx"]["inputs"][u_name]["quantization_parameters"]
                    f_val = (cn_dict[c_name].astype(np.float32) - p_c["zero_point"]) * p_c["scale"] * reference_fidelity
                    cn_residuals[u_name] = np.clip(np.round(f_val / p_u["scale"]) + p_u["zero_point"], 0, 65535).astype(np.uint16)

                p_cm = cn_meta["controlnet.onnx"]["outputs"]["mid_block"]["quantization_parameters"]
                p_um = cn_meta["unet.onnx"]["inputs"]["controlnet_midblock"]["quantization_parameters"]
                f_mid = (cn_dict["mid_block"].astype(np.float32) - p_cm["zero_point"]) * p_cm["scale"] * reference_fidelity
                cn_residuals["controlnet_midblock"] = np.clip(np.round(f_mid / p_um["scale"]) + p_um["zero_point"], 0, 65535).astype(np.uint16)

                # UNet pass (16 inputs)
                lat_q_u = np.clip(np.round(latent_model_input / p_lat_u["scale"]) + p_lat_u["zero_point"], 0, 65535).astype(np.uint16)
                t_q_u = np.clip(np.round(t / p_t_u["scale"]) + p_t_u["zero_point"], 0, 65535).astype(np.uint16)
                t_arr_u = np.array([[t_q_u]], dtype=np.uint16)

                unet_cond_in = {"latent": lat_q_u, "timestep": t_arr_u, "text_emb": cond_emb_unet, **cn_residuals}
                unet_uncond_in = {"latent": lat_q_u, "timestep": t_arr_u, "text_emb": uncond_emb_unet, **cn_residuals}

                t_unet_start = time.perf_counter()
                out_cond_q = unet_session.run(["output_latent"], unet_cond_in)[0]
                out_uncond_q = unet_session.run(["output_latent"], unet_uncond_in)[0]
                unet_step_times.append((time.perf_counter() - t_unet_start) * 1000.0)

                noise_pred_cond = (out_cond_q.astype(np.float32) - p_out_u["zero_point"]) * p_out_u["scale"]
                noise_pred_uncond = (out_uncond_q.astype(np.float32) - p_out_u["zero_point"]) * p_out_u["scale"]
            else:
                # Standard UNet pass (3 inputs)
                latent_quant = quantize_unet_latent(latent_model_input)
                t_quant = np.clip(
                    np.round(t / UNET_TIMESTEP_IN_SCALE) + UNET_TIMESTEP_IN_ZERO_POINT, 0, 65535
                ).astype(np.uint16)
                t_quant_arr = np.array([[t_quant]], dtype=np.uint16)

                t_unet_start = time.perf_counter()
                out_cond_q = unet_session.run(
                    ["output_latent"],
                    {"latent": latent_quant, "timestep": t_quant_arr, "text_emb": cond_emb_unet},
                )[0]
                out_uncond_q = unet_session.run(
                    ["output_latent"],
                    {"latent": latent_quant, "timestep": t_quant_arr, "text_emb": uncond_emb_unet},
                )[0]
                unet_step_times.append((time.perf_counter() - t_unet_start) * 1000.0)

                noise_pred_cond = (
                    out_cond_q.astype(np.float32) - UNET_LATENT_OUT_ZERO_POINT
                ) * UNET_LATENT_OUT_SCALE
                noise_pred_uncond = (
                    out_uncond_q.astype(np.float32) - UNET_LATENT_OUT_ZERO_POINT
                ) * UNET_LATENT_OUT_SCALE

            # Classifier Free Guidance
            noise_pred = noise_pred_uncond + cfg_scale * (noise_pred_cond - noise_pred_uncond)

            # Euler step
            dt = next_sigma - sigma
            latents_generated = latents + noise_pred * dt

            if mode == "img2img":
                if is_latent_anchor:
                    w_k = float(reference_fidelity * ((sigma / sigma_start) ** 2))
                    if next_sigma > 0.0:
                        anchor = z_ref0 + noise * next_sigma
                    else:
                        anchor = z_ref0
                    latents = (1.0 - w_k) * latents_generated + w_k * anchor
                else:
                    latents = latents_generated
            else:
                # Latent Blending Step (RePaint / Latent Replacement)
                if next_sigma > 0.0:
                    orig_noisy = z0 + noise * next_sigma
                    latents = mask_latent * latents_generated + (1.0 - mask_latent) * orig_noisy
                else:
                    latents = mask_latent * latents_generated + (1.0 - mask_latent) * z0

        t_unet_total_ms = sum(unet_step_times)

        # 8. Qualcomm Hexagon HTP VAE Decoding
        report("vae_decode", 0.90, "Bild dekodieren (HTP VAE-Decoder)...")
        # Re-quantize latents for VAE Decoder input
        latents_vae_quant = quantize_decoder_latent(latents)

        t_vae_start = time.perf_counter()
        image_quant = vae_session.run(["image"], {"latent": latents_vae_quant})[0]
        t_vae_ms = (time.perf_counter() - t_vae_start) * 1000.0

        # Dequantize VAE output
        image_float = (
            image_quant.astype(np.float32) - VAE_DECODER_OUT_ZERO_POINT
        ) * VAE_DECODER_OUT_SCALE
        generated_rgb = np.clip(image_float[0] * 255.0, 0, 255).astype(np.uint8)
        generated_img = Image.fromarray(generated_rgb)

        # 9. Output Composition & Saving
        if mode == "img2img":
            report("saving", 0.95, "Ergebnisbild speichern...")
            final_img = generated_img
        else:
            report("composite", 0.95, "Pixelgenaue Komposition mit Kantenglättung...")
            feathered_mask = generate_feathered_mask(
                mask_img,
                dilate_pixels=dilate_pixels,
                feather_radius=feather_radius,
            )
            aligned_gen = align_color_lab(
                source_img=source_img,
                generated_img=generated_img,
                mask_img=mask_img,
                dilate_pixels=dilate_pixels,
                feather_radius=feather_radius,
            )
            final_img = Image.composite(aligned_gen, source_img, feathered_mask)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_img.save(output_path, format="PNG")

        # Save Gallery Sidecar JSON
        sidecar_path = output_path.with_suffix(".json")
        sidecar_dict = {
            "feature": "Image-to-Image" if mode == "img2img" else "AI Inpainting",
            "mode": mode,
            "mode": mode,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "model": "stable_diffusion_v1_5_qnn",
            "width": 512,
            "height": 512,
            "steps": steps,
            "actual_steps": num_inference_steps,
            "cfg": cfg_scale,
            "seed": seed,
            "denoising_strength": denoising_strength,
            "sampler": "Euler",
            "backend": "Qualcomm SD1.5 QNN (HTP)",
            "input_image_path": str(input_image_path),
            "output_path": str(output_path),
            "reference_control": {
                "enabled": is_ref_control,
                "mode": reference_mode if is_ref_control else "none",
                "fidelity": reference_fidelity if is_ref_control else 0.0,
                "reference_image": str(reference_image_path) if is_ref_control else None,
            },
            "total_seconds": (t_enc_ms + t_text_ms + (sum(cn_step_times) if cn_step_times else 0.0) + t_unet_total_ms + t_vae_ms) / 1000.0,
        }
        try:
            with open(sidecar_path, "w", encoding="utf-8") as f_sc:
                json.dump(sidecar_dict, f_sc, indent=2)
        except Exception as e_sc:
            logger.warning("Could not write sidecar JSON %s: %s", sidecar_path, e_sc)

        report("complete", 1.0, "Generierung erfolgreich abgeschlossen.")

        metadata = {
            "mode": mode,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": steps,
            "seed": seed,
            "cfg_scale": cfg_scale,
            "feather_radius": feather_radius,
            "dilate_pixels": dilate_pixels,
            "denoising_strength": denoising_strength,
            "actual_inference_steps": num_inference_steps,
            "reference_control": {
                "enabled": is_ref_control,
                "mode": reference_mode if is_ref_control else "none",
                "fidelity": reference_fidelity if is_ref_control else 0.0,
                "reference_image": str(reference_image_path) if is_ref_control else None,
            },
            "execution_times": {
                "htp_vae_encoder_ms": t_enc_ms,
                "cpu_vae_encoder_ms": 0.0,
                "htp_clip_text_ms": t_text_ms,
                "htp_controlnet_total_ms": sum(cn_step_times) if cn_step_times else 0.0,
                "htp_unet_total_ms": t_unet_total_ms,
                "htp_unet_step_avg_ms": float(np.mean(unet_step_times)) if unet_step_times else 0.0,
                "htp_vae_decoder_ms": t_vae_ms,
                "total_inference_ms": t_enc_ms + t_text_ms + (sum(cn_step_times) if cn_step_times else 0.0) + t_unet_total_ms + t_vae_ms,
            },
            "device": "Qualcomm Hexagon HTP V73",
            "disable_cpu_fallback": True,
            "all_stages_on_htp": True,
            "unet_calls_count": num_inference_steps * 2,
        }

        return SD15QnnInpaintingResult(
            success=True,
            output=np.array(final_img, dtype=np.uint8),
            output_path=output_path,
            backend_name="sd15_qnn_htp",
            metadata=metadata,
        )


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                job_dict = json.load(f)

            adapter = SD15QnnInpaintingAdapter()
            result = adapter._execute_in_process(job_dict)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "success": result.success,
                        "output_path": str(result.output_path) if result.output_path else None,
                        "error_code": result.error_code,
                        "error_message": result.error_message,
                        "backend_name": result.backend_name,
                        "metadata": result.metadata,
                    },
                    f,
                    indent=2,
                )
            sys.exit(0 if result.success else 1)
        except Exception as err:
            logger.exception("Subprocess inpainting execution failed")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"success": False, "error_code": "ERR_UNHANDLED", "error_message": str(err)}, f, indent=2)
            sys.exit(1)
