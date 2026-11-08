"""
Phoenix Material Lab – Standalone Photometric Material Priming Module.
HK NPU STUDIO (Phoenix Architecture)

Transforms object materials (e.g. glass to 24k gold, antique brass, copper, chrome)
while preserving exact geometry, diffuse lighting, contours, and specular shading.
Executes non-destructively in pure vectorized NumPy/PIL math without CPU generative inference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class MaterialPreset:
    """Specification of a physical material preset for photometric priming."""
    id: str
    display_name: str
    hue_deg: float
    sat_min: float
    sat_max: float
    val_multiplier: float
    metallic_contrast: float
    recommended_prompt: str
    negative_prompt: str
    min_val: float = 0.0


MATERIAL_PRESETS: dict[str, MaterialPreset] = {
    "24k_gold": MaterialPreset(
        id="24k_gold",
        display_name="24k Gold",
        hue_deg=40.0,
        sat_min=130.0,
        sat_max=220.0,
        val_multiplier=1.05,
        metallic_contrast=1.05,
        recommended_prompt=(
            "A solid polished 24k gold modern table sculpture, sleek smooth curved metallic shape, "
            "pure 24k yellow gold metal, highly reflective golden surface, heavy solid gold, "
            "warm natural highlights, photorealistic, elegant tabletop centerpiece."
        ),
        negative_prompt=(
            "seam, black line, dark slit, crease, shadow line, border line, gap, crack, rift, "
            "dent, dented, crater, cavity, hole, dark spot, depression, blemish, black pit, bite mark, "
            "glass, transparent, translucent, green, blue, turquoise, bird, falcon, animal, "
            "feathers, beak, white wall, room divider, wooden furniture, plants, people, blurry, deformed."
        ),
        min_val=195.0,
    ),
    "antique_brass": MaterialPreset(
        id="antique_brass",
        display_name="Antik-Messing",
        hue_deg=56.0,
        sat_min=85.0,
        sat_max=175.0,
        val_multiplier=1.02,
        metallic_contrast=1.02,
        recommended_prompt=(
            "A solid polished antique brass modern table sculpture, sleek smooth curved metallic shape, "
            "rich warm brass metal, subtle aged patina, warm natural highlights, "
            "photorealistic, elegant tabletop centerpiece."
        ),
        negative_prompt=(
            "dent, dented, crater, cavity, hole, dark spot, depression, blemish, black pit, bite mark, "
            "glass, transparent, translucent, green, blue, turquoise, bird, falcon, animal, "
            "feathers, beak, white wall, room divider, wooden furniture, plants, people, blurry, deformed."
        ),
    ),
    "copper": MaterialPreset(
        id="copper",
        display_name="Kupfer",
        hue_deg=18.0,
        sat_min=145.0,
        sat_max=235.0,
        val_multiplier=1.04,
        metallic_contrast=1.04,
        recommended_prompt=(
            "A solid polished copper modern table sculpture, sleek smooth curved metallic shape, "
            "pure reddish copper metal, reflective metallic copper surface, warm natural highlights, "
            "photorealistic, elegant tabletop centerpiece."
        ),
        negative_prompt=(
            "dent, dented, crater, cavity, hole, dark spot, depression, blemish, black pit, bite mark, "
            "glass, transparent, translucent, green, blue, turquoise, bird, falcon, animal, "
            "feathers, beak, white wall, room divider, wooden furniture, plants, people, blurry, deformed."
        ),
    ),
    "chrome": MaterialPreset(
        id="chrome",
        display_name="Chrom",
        hue_deg=0.0,
        sat_min=0.0,
        sat_max=15.0,
        val_multiplier=1.15,
        metallic_contrast=1.12,
        recommended_prompt=(
            "A solid polished mirror chrome modern table sculpture, sleek smooth curved metallic shape, "
            "pure silver chrome metal, mirror reflective surface, specular highlights, "
            "photorealistic, elegant tabletop centerpiece."
        ),
        negative_prompt=(
            "dent, dented, crater, cavity, hole, dark spot, depression, blemish, black pit, bite mark, "
            "glass, transparent, translucent, green, blue, turquoise, bird, falcon, animal, "
            "feathers, beak, white wall, room divider, wooden furniture, plants, people, blurry, deformed."
        ),
    ),
    "black_leather": MaterialPreset(
        id="black_leather",
        display_name="Schwarzes Leder",
        hue_deg=0.0,
        sat_min=0.0,
        sat_max=2.0,
        val_multiplier=0.28,
        metallic_contrast=1.05,
        recommended_prompt=(
            "A photorealistic black leather jacket, authentic fine leather grain texture, "
            "subtle specular highlights, professional studio lighting, 8k."
        ),
        negative_prompt=(
            "red, crimson, burgundy, wine, red tint, fabric, cloth, cotton, blurry, distorted, cartoon, low quality"
        ),
        min_val=30.0,
    ),
}

# Aliases for robust resolution
_PRESET_ALIASES: dict[str, str] = {
    "gold": "24k_gold",
    "24k gold": "24k_gold",
    "24k_gold": "24k_gold",
    "brass": "antique_brass",
    "antique_brass": "antique_brass",
    "antik-messing": "antique_brass",
    "antik messing": "antique_brass",
    "messing": "antique_brass",
    "copper": "copper",
    "kupfer": "copper",
    "chrome": "chrome",
    "chrom": "chrome",
    "silver": "chrome",
    "silber": "chrome",
    "leather": "black_leather",
    "black_leather": "black_leather",
    "schwarzes leder": "black_leather",
    "schwarzes_leder": "black_leather",
    "leder": "black_leather",
}


def list_material_presets() -> list[str]:
    """Return list of standard material preset IDs."""
    return list(MATERIAL_PRESETS.keys())


def get_material_preset(name: str) -> MaterialPreset:
    """
    Resolve a material preset by ID or alias.
    Raises KeyError if unknown preset name.
    """
    normalized = name.strip().lower()
    canonical_id = _PRESET_ALIASES.get(normalized, normalized)
    if canonical_id in MATERIAL_PRESETS:
        return MATERIAL_PRESETS[canonical_id]
    raise KeyError(f"Unknown material preset: '{name}'. Available: {list_material_presets()}")


def prime_material_chrominance(
    source_img: Image.Image,
    mask_img: Image.Image,
    preset_name: str = "24k_gold",
    intensity: float = 1.0,
) -> Image.Image:
    """
    Apply photometric material priming to the masked region of source_img.

    Args:
        source_img: Original image in RGB mode.
        mask_img: Inpainting mask (L mode or convertable). Values > 0 are modified.
        preset_name: Material preset ('24k_gold', 'antique_brass', 'copper', 'chrome').
        intensity: Blending intensity (0.0 = unchanged, 1.0 = full material priming).

    Returns:
        New PIL Image with the primed material in the masked zone, with
        bit-exact preservation outside the mask (MSE = 0.000000).
    """
    preset = get_material_preset(preset_name)
    intensity = max(0.0, min(1.0, float(intensity)))

    if source_img.mode != "RGB":
        source_img = source_img.convert("RGB")
    if mask_img.mode != "L":
        mask_img = mask_img.convert("L")

    if mask_img.size != source_img.size:
        raise ValueError(
            f"Mask size {mask_img.size} does not match source image size {source_img.size}"
        )

    orig_arr = np.array(source_img, dtype=np.float32)
    mask_arr = np.array(mask_img, dtype=np.float32) / 255.0

    # If mask is completely empty, return copy of original immediately
    if not np.any(mask_arr > 0.0) or intensity == 0.0:
        return source_img.copy()

    # Convert source to HSV for photometric decomposition
    orig_hsv = np.array(source_img.convert("HSV"), dtype=np.float32)
    h = orig_hsv[:, :, 0]  # [0..255] representing [0..360 deg]
    s = orig_hsv[:, :, 1]  # [0..255]
    v = orig_hsv[:, :, 2]  # [0..255]
    v_norm = v / 255.0

    # 1. Target Hue
    target_h = float(preset.hue_deg * 255.0 / 360.0)
    prime_h = np.full_like(h, target_h)

    # 3. Target Value (preserving original lighting, applying metallic tone curve & luminance compression)
    if preset.min_val > 0.0:
        norm_comp = (preset.min_val / 255.0) + v_norm * (1.0 - (preset.min_val / 255.0))
        prime_v = np.clip(norm_comp * 255.0 * preset.val_multiplier, 0.0, 255.0)
    else:
        prime_v = np.clip(v * preset.val_multiplier, 0.0, 255.0)

    # 2. Target Saturation (modulated by luminance to preserve specular metallic rolloff)
    # Midtones have maximum saturation; very dark and bright highlights roll off naturally
    sat_curve = np.sin(np.pi * np.clip(prime_v / 255.0, 0.0, 1.0))
    target_s = preset.sat_min + (preset.sat_max - preset.sat_min) * sat_curve
    prime_s = np.clip(target_s, 0.0, 255.0)

    # Stack into primed HSV image
    hsv_primed = np.stack([prime_h, prime_s, prime_v], axis=-1).astype(np.uint8)
    rgb_primed = np.array(Image.fromarray(hsv_primed, mode="HSV").convert("RGB"), dtype=np.float32)

    # Effective blend factor = mask * intensity
    alpha = np.clip(mask_arr * intensity, 0.0, 1.0)[:, :, np.newaxis]

    # Non-destructive Alpha Compositing:
    # Strictly ensures that outside the mask (alpha == 0), result is identical to source
    out_arr = orig_arr * (1.0 - alpha) + rgb_primed * alpha
    out_uint8 = np.clip(np.round(out_arr), 0, 255).astype(np.uint8)

    # Exact bit-preservation guarantee outside mask
    unmasked = mask_arr == 0.0
    out_uint8[unmasked] = np.round(orig_arr[unmasked]).astype(np.uint8)

    return Image.fromarray(out_uint8, mode="RGB")
