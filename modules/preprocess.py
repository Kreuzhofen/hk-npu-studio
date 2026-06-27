from pathlib import Path
import numpy as np
from PIL import Image
from config import TILE_SIZE

def tile_to_raw(tile: Image.Image, raw_path: Path) -> None:
    raw_path = Path(raw_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    tile = tile.convert("RGB")
    if tile.size != (TILE_SIZE, TILE_SIZE):
        tile = tile.resize((TILE_SIZE, TILE_SIZE))
    arr = np.asarray(tile).astype(np.float32) / 255.0
    arr = arr.reshape(1, TILE_SIZE, TILE_SIZE, 3)
    arr.tofile(raw_path)
