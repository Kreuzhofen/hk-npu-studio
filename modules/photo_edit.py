from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

def apply_adjustments(
    input_path: Path,
    output_path: Path,
    brightness: float = 1.0,
    contrast: float = 1.0,
    color: float = 1.0,
    sharpness: float = 1.0,
    warm: float = 0.0,
) -> Path:
    img = Image.open(input_path).convert("RGB")

    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(color)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)

    if warm != 0:
        r, g, b = img.split()
        r = r.point(lambda i: max(0, min(255, i + warm * 18)))
        b = b.point(lambda i: max(0, min(255, i - warm * 10)))
        img = Image.merge("RGB", (r, g, b))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path
