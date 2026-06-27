from pathlib import Path

BASE = Path(r"C:\SnapdragonAI")
INPUT_DIR = BASE / "input"
OUTPUT_DIR = BASE / "output"
TEMP_DIR = BASE / "temp"
MODELS_DIR = BASE / "models"
PLUGINS_DIR = BASE / "plugins"
WORKFLOWS_DIR = BASE / "workflows"

COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8188
COMFYUI_BASE_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

QNN_BIN = Path(r"C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-net-run.exe")
QNN_BACKEND = Path(r"C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll")
QNN_LIB_DIR = Path(r"C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc")
QNN_BIN_DIR = Path(r"C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc")

REALESRGAN_MODEL = MODELS_DIR / "real_esrgan_x4plus.bin"

TILE_SIZE = 128
SCALE = 4
OUT_TILE_SIZE = TILE_SIZE * SCALE
REALESRGAN_OUTPUT_SHAPE = (1, OUT_TILE_SIZE, OUT_TILE_SIZE, 3)
