import sys
import os
import subprocess
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

QNN_BIN = r"C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-net-run.exe"
QNN_BACKEND = r"C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll"
MODEL = r"C:\SnapdragonAI\models\real_esrgan_x4plus.bin"

BASE = r"C:\SnapdragonAI"
INPUT_DIR = os.path.join(BASE, "input")
OUTPUT_DIR = os.path.join(BASE, "output")

RAW_INPUT = os.path.join(INPUT_DIR, "image.raw")
INPUT_LIST = os.path.join(INPUT_DIR, "input_list.txt")
RESULT_RAW = os.path.join(OUTPUT_DIR, "Result_0", "upscaled_image.raw")
RESULT_PNG = os.path.join(OUTPUT_DIR, "upscaled_image.png")

if len(sys.argv) < 2:
    print("Bitte ein Bild angeben, z.B.: python run_realesrgan.py bild.jpg")
    sys.exit(1)

image_path = sys.argv[1]

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

img = Image.open(image_path).convert("RGB")
img = img.resize((128, 128))
arr = np.asarray(img).astype(np.float32) / 255.0
arr = arr.reshape(1, 128, 128, 3)
arr.tofile(RAW_INPUT)

with open(INPUT_LIST, "w", encoding="utf-8") as f:
    f.write(RAW_INPUT)

env = os.environ.copy()
env["PATH"] = (
    r"C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc;"
    r"C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc;"
    + env["PATH"]
)

cmd = [
    QNN_BIN,
    "--retrieve_context", MODEL,
    "--backend", QNN_BACKEND,
    "--input_list", INPUT_LIST,
    "--output_dir", OUTPUT_DIR,
    "--log_level", "info",
]

print("Starte NPU...")
subprocess.run(cmd, env=env, check=True)

out = np.fromfile(RESULT_RAW, dtype=np.float32).reshape(1, 512, 512, 3)[0]
out = np.clip(out * 255, 0, 255).astype(np.uint8)
img_out = Image.fromarray(out)

# Restore correct aspect ratio (RealESRGAN x4)
from PIL import ImageOps
with Image.open(image_path) as orig:
    orig_transposed = ImageOps.exif_transpose(orig)
    orig_w, orig_h = orig_transposed.size
target_w = orig_w * 4
target_h = orig_h * 4
img_out = img_out.resize((target_w, target_h), resample=Image.Resampling.LANCZOS)
img_out.save(RESULT_PNG)

print("Fertig:")
print(RESULT_PNG)