from pathlib import Path
import numpy as np
from PIL import Image
from config import REALESRGAN_OUTPUT_SHAPE

def raw_tile_to_image(raw_path: Path) -> Image.Image:
    raw_path = Path(raw_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"RAW-Ausgabe nicht gefunden: {raw_path}")
    arr = np.fromfile(raw_path, dtype=np.float32).reshape(REALESRGAN_OUTPUT_SHAPE)[0]
    arr = np.clip(arr * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)
