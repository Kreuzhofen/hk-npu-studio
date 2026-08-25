from pathlib import Path
from engine.file_utils import get_unique_filename
import math
import time
from PIL import Image, ImageChops
from config import OUTPUT_DIR, TEMP_DIR, TILE_SIZE, SCALE
from modules.preprocess import tile_to_raw
from modules.qnn import run_qnn_context
from modules.postprocess import raw_tile_to_image


TILE_OVERLAP = 16


def tile_positions(length: int, tile_size: int = TILE_SIZE, overlap: int = TILE_OVERLAP) -> list[int]:
    """Distribute fixed-size tiles across an axis without a redundant final tile."""
    if length <= tile_size:
        return [0]
    stride = tile_size - overlap
    tile_count = math.ceil((length - tile_size) / stride) + 1
    final_position = length - tile_size
    intervals = tile_count - 1
    return [index * final_position // intervals for index in range(tile_count)]


def tile_overlaps(
    x_positions: list[int],
    y_positions: list[int],
    x_index: int,
    y_index: int,
    tile_width: int,
    tile_height: int,
) -> tuple[int, int, int, int]:
    """Return the actual left, right, top, and bottom overlap for one tile."""
    x = x_positions[x_index]
    y = y_positions[y_index]
    left = max(0, x_positions[x_index - 1] + tile_width - x) if x_index else 0
    right = max(0, x + tile_width - x_positions[x_index + 1]) if x_index + 1 < len(x_positions) else 0
    top = max(0, y_positions[y_index - 1] + tile_height - y) if y_index else 0
    bottom = max(0, y + tile_height - y_positions[y_index + 1]) if y_index + 1 < len(y_positions) else 0
    return left, right, top, bottom


def feather_mask(width: int, height: int, left_overlap: int, top_overlap: int) -> Image.Image:
    """Create a local blend mask; future tiles blend over right and bottom edges."""
    mask = Image.new("L", (width, height), 255)
    if left_overlap:
        left_width = min(left_overlap, width)
        gradient = Image.new("L", (left_width, 1))
        gradient.putdata([round(255 * (index + 1) / left_width) for index in range(left_width)])
        mask.paste(gradient.resize((left_width, height)), (0, 0))
    if top_overlap:
        top_height = min(top_overlap, height)
        gradient = Image.new("L", (1, top_height))
        gradient.putdata([round(255 * (index + 1) / top_height) for index in range(top_height)])
        top_mask = Image.new("L", (width, height), 255)
        top_mask.paste(gradient.resize((width, top_height)), (0, 0))
        mask = ImageChops.multiply(mask, top_mask)
    return mask

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

    x_positions = tile_positions(width)
    y_positions = tile_positions(height)
    tiles_x = len(x_positions)
    tiles_y = len(y_positions)
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

            left = x_positions[tx]
            top = y_positions[ty]
            right = min(left + TILE_SIZE, width)
            bottom = min(top + TILE_SIZE, height)

            tile = image.crop((left, top, right, bottom))
            padded_tile, tile_w, tile_h = pad_tile(tile)
            left_overlap, right_overlap, top_overlap, bottom_overlap = tile_overlaps(
                x_positions, y_positions, tx, ty, tile_w, tile_h
            )

            _log(f"[{tile_index}/{total_tiles}] Kachel x={tx+1}/{tiles_x}, y={ty+1}/{tiles_y}")

            upscaled_tile = run_tile(padded_tile, work_dir, tile_index)
            upscaled_tile = upscaled_tile.crop((0, 0, tile_w*SCALE, tile_h*SCALE))
            mask = feather_mask(
                upscaled_tile.width,
                upscaled_tile.height,
                left_overlap * SCALE,
                top_overlap * SCALE,
            )
            destination = (left * SCALE, top * SCALE)
            existing = result.crop((
                destination[0], destination[1],
                destination[0] + upscaled_tile.width, destination[1] + upscaled_tile.height,
            ))
            result.paste(Image.composite(upscaled_tile, existing, mask), destination)

    _percent(98)
    output_path = get_unique_filename(OUTPUT_DIR, f"{image_path.stem}_tile_upscaled_x4.png")
    result.save(output_path)
    _status("Fertig")
    _percent(100)
    _progress("100 %")
    _log(f"Fertig: {output_path}")
    return output_path
