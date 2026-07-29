from pathlib import Path

BASE = Path(r"C:\SnapdragonAI")
INPUT_DIR = BASE / "input"
OUTPUT_DIR = BASE / "output"
DATA_DIR = BASE / "data"
LOG_DIR = BASE / "logs"
ASSET_INDEX_DB = DATA_DIR / "asset_index.sqlite3"
PREFERENCES_PATH = DATA_DIR / "preferences.json"
PROMPT_HISTORY_PATH = DATA_DIR / "prompt_history.json"
PROMPT_TEMPLATES_PATH = BASE / "resources" / "prompt_templates.json"
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

LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5

import json
import os

HF_TOKEN = ""
try:
    if PREFERENCES_PATH.exists():
        with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                HF_TOKEN = data.get("hf_token", "")
except Exception:
    pass

if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN

