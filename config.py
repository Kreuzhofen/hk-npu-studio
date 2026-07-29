import os
import sys
from pathlib import Path

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
USER_BASE = (
    Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    / "Snapdragon AI Studio"
    if getattr(sys, "frozen", False)
    else BASE
)
INPUT_DIR = USER_BASE / "input"
OUTPUT_DIR = USER_BASE / "output"
DATA_DIR = USER_BASE / "data"
LOG_DIR = USER_BASE / "logs"
ASSET_INDEX_DB = DATA_DIR / "asset_index.sqlite3"
PREFERENCES_PATH = DATA_DIR / "preferences.json"
PROMPT_HISTORY_PATH = DATA_DIR / "prompt_history.json"
PROMPT_TEMPLATES_PATH = BASE / "resources" / "prompt_templates.json"
TEMP_DIR = USER_BASE / "temp"
MODELS_DIR = USER_BASE / "models"
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

import os
from app.configuration_manager import ConfigurationManager

_PREFERENCES = ConfigurationManager(PREFERENCES_PATH).load()
HF_TOKEN = str(_PREFERENCES.get("hf_token", ""))

if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN

