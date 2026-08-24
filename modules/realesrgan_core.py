from pathlib import Path
from engine.file_utils import get_unique_filename
import math
import time
from PIL import Image
from config import OUTPUT_DIR, TEMP_DIR, TILE_SIZE, SCALE
from modules.preprocess import tile_to_raw
from modules.qnn import run_qnn_context
from modules.postprocess import raw_tile_to_image

def pad_tile(tile: Image.Image):
    original_w, original_h = tile.size
    if original_w == TILE_SIZE and original_h == TILE_SIZE:
        return tile, original_w, original_h
    padded = Image.new("RGB", (TILE_SIZE, TILE_SIZE))
    padded.paste(tile, (0, 0))
    if original_w < TILE_SIZE:
        right_strip = tile.crop((original_w - 1, 0, original_w, original_h))
        for x in range(original_w, TILE_SIZE):
            padded.paste(right_strip, (x, 0))
    if original_h < TILE_SIZE:
        bottom_strip = padded.crop((0, original_h - 1, TILE_SIZE, original_h))
        for y in range(original_h, TILE_SIZE):
            padded.paste(bottom_strip, (0, y))
    return padded, original_w, original_h

def run_tile(tile: Image.Image, work_dir: Path, tile_index: int) -> Image.Image:
    tile_dir = work_dir / f"tile_{tile_index:05d}"
    input_dir = tile_dir / "input"
    output_dir = tile_dir / "output"
    raw_input = input_dir / "image.raw"
    input_list = input_dir / "input_list.txt"
    tile_to_raw(tile, raw_input)
    input_list.write_text(raw_input.name, encoding="utf-8")
    run_qnn_context(input_list, output_dir, log_level="error")
    result_raw = output_dir / "Result_0" / "upscaled_image.raw"
    return raw_tile_to_image(result_raw)

def upscale_tiled(image_path: Path, log=None, progress=None, status=None, percent=None) -> Path:
    image_path = Path(image_path)

    def _log(msg):
        log(msg) if log else print(msg)
    def _progress(msg):
        if progress: progress(msg)
    def _status(msg):
        if status: status(msg)
    def _percent(value):
        if percent: percent(value)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    _status("Bild wird geladen...")
    _log("Bild wird geladen...")
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    tiles_x = math.ceil(width / TILE_SIZE)
    tiles_y = math.ceil(height / TILE_SIZE)
    total_tiles = tiles_x * tiles_y

    _log(f"Original: {width} x {height}")
    _log(f"Ausgabe:  {width*SCALE} x {height*SCALE}")
    _log(f"Kacheln:  {tiles_x} x {tiles_y} = {total_tiles}")

    work_dir = TEMP_DIR / f"realesrgan_tiles_{time.strftime('%Y%m%d_%H%M%S')}"
    work_dir.mkdir(parents=True, exist_ok=True)

    result = Image.new("RGB", (width*SCALE, height*SCALE))
    tile_index = 0

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            tile_index += 1
            current_percent = (tile_index - 1) / total_tiles * 100
            _percent(current_percent)
            _status("NPU-Upscaling läuft...")
            _progress(f"{current_percent:.0f} %  ·  Kachel {tile_index}/{total_tiles}")

            left = tx * TILE_SIZE
            top = ty * TILE_SIZE
            right = min(left + TILE_SIZE, width)
            bottom = min(top + TILE_SIZE, height)

            tile = image.crop((left, top, right, bottom))
            padded_tile, tile_w, tile_h = pad_tile(tile)

            _log(f"[{tile_index}/{total_tiles}] Kachel x={tx+1}/{tiles_x}, y={ty+1}/{tiles_y}")

            upscaled_tile = run_tile(padded_tile, work_dir, tile_index)
            upscaled_tile = upscaled_tile.crop((0, 0, tile_w*SCALE, tile_h*SCALE))
            result.paste(upscaled_tile, (left*SCALE, top*SCALE))

    _percent(98)
    output_path = get_unique_filename(OUTPUT_DIR, f"{image_path.stem}_tile_upscaled_x4.png")
    result.save(output_path)
    _status("Fertig")
    _percent(100)
    _progress("100 %")
    _log(f"Fertig: {output_path}")
    return output_path
