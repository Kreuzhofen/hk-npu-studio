from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
from PIL import Image, ImageFilter


@dataclass(frozen=True)
class PhoenixBoostQualityResult:
    image: Image.Image
    profile: str
    raw_sha256: str
    boosted_sha256: str


class PhoenixBoostQualityPass:
    """Deterministic, non-neural finishing pass for generated RGB images."""

    _PAINTING_MARKERS = (
        "painting", "painted", "oil paint", "renaissance", "watercolor",
        "aquarell", "gemälde", "malerei", "pintura", "acuarela",
    )
    _PORTRAIT_MARKERS = (
        "portrait", "porträt", "retrato", "woman", "man", "person",
        "frau", "mann", "person", "mujer", "hombre", "bride", "groom",
    )
    _PHOTO_MARKERS = ("photo", "photograph", "fotografie", "foto", "photorealistic")
    _PROFILE = {
        "PHOTO": (1.35, 0.42, 0.052),
        "PORTRAIT_PHOTO": (1.45, 0.40, 0.040),
        "ART_PAINTING": (1.10, 0.32, 0.038),
        "GENERAL": (1.30, 0.30, 0.034),
    }

    @classmethod
    def classify(cls, prompt: str) -> str:
        value = prompt.casefold()
        if any(marker in value for marker in cls._PAINTING_MARKERS):
            return "ART_PAINTING"
        if (
            any(marker in value for marker in cls._PORTRAIT_MARKERS)
            and any(marker in value for marker in cls._PHOTO_MARKERS)
        ):
            return "PORTRAIT_PHOTO"
        if any(marker in value for marker in cls._PHOTO_MARKERS):
            return "PHOTO"
        return "GENERAL"

    @staticmethod
    def pixel_sha256(image: Image.Image) -> str:
        canonical = image.convert("RGBA") if image.mode == "RGBA" else image.convert("RGB")
        payload = (
            canonical.mode.encode("ascii")
            + b"\0"
            + str(canonical.size).encode("ascii")
            + b"\0"
            + canonical.tobytes()
        )
        return hashlib.sha256(payload).hexdigest().upper()

    @classmethod
    def apply(cls, source: Image.Image, prompt: str) -> PhoenixBoostQualityResult:
        profile = cls.classify(prompt)
        radius, amount, max_delta = cls._PROFILE[profile]

        alpha = source.getchannel("A").copy() if source.mode == "RGBA" else None
        rgb_image = source.convert("RGB")
        raw_hash = cls.pixel_sha256(source)
        rgb = np.asarray(rgb_image, dtype=np.float32) / 255.0
        luminance = (
            rgb[..., 0] * 0.2126
            + rgb[..., 1] * 0.7152
            + rgb[..., 2] * 0.0722
        )
        luminance_u8 = Image.fromarray(
            np.clip(np.rint(luminance * 255.0), 0, 255).astype(np.uint8),
            mode="L",
        )
        local_mean = np.asarray(
            luminance_u8.filter(ImageFilter.GaussianBlur(radius=radius)),
            dtype=np.float32,
        ) / 255.0

        # Luminance-only, tapered clarity preserves hue/chroma and protects deep
        # shadows/highlights from clipping or visible edge overshoot.
        detail = luminance - local_mean
        tonal_weight = np.clip(4.0 * luminance * (1.0 - luminance), 0.0, 1.0)
        delta = np.clip(detail * amount * tonal_weight, -max_delta, max_delta)
        quantization_margin = 0.51 / 255.0
        headroom = np.maximum(
            np.minimum(rgb.min(axis=2), 1.0 - rgb.max(axis=2)) - quantization_margin,
            0.0,
        )
        delta = np.clip(delta, -headroom, headroom)
        boosted_rgb = np.clip(rgb + delta[..., None], 0.0, 1.0)
        boosted = Image.fromarray(
            np.clip(np.rint(boosted_rgb * 255.0), 0, 255).astype(np.uint8),
            mode="RGB",
        )
        if alpha is not None:
            boosted.putalpha(alpha)

        return PhoenixBoostQualityResult(
            image=boosted,
            profile=profile,
            raw_sha256=raw_hash,
            boosted_sha256=cls.pixel_sha256(boosted),
        )
