"""
Sprint 79 - Inspection of input image 'rote jacke.jpg'
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

INPUT_PATH = Path(r"C:\Users\holge\Desktop\Testbilder\rote jacke.jpg")
DEST_DIR = Path(r"C:\SnapdragonAI\reports\sprint_79_red_jacket\images")
DEST_DIR.mkdir(parents=True, exist_ok=True)
DEST_PATH = DEST_DIR / "original_rote_jacke.jpg"

shutil.copy2(INPUT_PATH, DEST_PATH)

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

sha = sha256_of_file(INPUT_PATH)
dest_sha = sha256_of_file(DEST_PATH)
assert sha == dest_sha

with Image.open(DEST_PATH) as img:
    format_name = img.format
    size = img.size
    mode = img.mode
    arr = np.array(img.convert("RGB"))

print(f"File: {INPUT_PATH}")
print(f"SHA-256: {sha}")
print(f"Format: {format_name}")
print(f"Dimensions: {size[0]} x {size[1]} (width x height)")
print(f"Color Mode: {mode}")
print(f"Array shape: {arr.shape}, dtype: {arr.dtype}")
print(f"Saved copy to: {DEST_PATH}")
