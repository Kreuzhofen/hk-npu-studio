from pathlib import Path
from modules.realesrgan_core import upscale_tiled

def upscale_image_gui(image_path: Path, log_callback=None, status_callback=None, progress_callback=None, percent_callback=None) -> Path:
    return upscale_tiled(
        image_path,
        log=log_callback,
        status=status_callback,
        progress=progress_callback,
        percent=percent_callback,
    )
