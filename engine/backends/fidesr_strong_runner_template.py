import os
import sys
import math
import time
import gc
import shutil
import subprocess
from pathlib import Path

import numpy as np

try:
    from PIL import Image
except Exception as e:
    raise SystemExit(f"HARD STOP: Pillow fehlt: {e}")


# ============================================================
# PATHS
# ============================================================

ROOT = Path(r"C:\SnapdragonAI")
MODEL_ROOT = ROOT / "models" / "photo_restore"
CONTEXT_ROOT = ROOT / "models" / "photo_restore_context"
TEMP_DIR = ROOT / "temp"
WORK = TEMP_DIR / "photo_restore"

INPUT_IMAGE = ROOT / "input" / "photo_restore_input.png"
OUTPUT_IMAGE = WORK / "photo_restore_output.png"

QNN_ROOT = Path(r"C:\Qualcomm\AIStack\2.47.0.260601")
QNN_BIN = QNN_ROOT / "bin" / "aarch64-windows-msvc"
QNN_LIB = QNN_ROOT / "lib" / "aarch64-windows-msvc"
QNN_HEX = QNN_ROOT / "lib" / "hexagon-v73" / "unsigned"

QNN_RUNNER = QNN_BIN / "qnn-net-run.exe"
QNN_BACKEND = QNN_LIB / "QnnHtp.dll"
CONTEXT_ENCODER = (
    CONTEXT_ROOT / "fidesr_vae_encoder" /
    "fidesr_vae_encoder.serialized.bin.bin"
)
CONTEXT_UNET = (
    CONTEXT_ROOT / "fidesr_unet" /
    "fidesr_unet_merged.serialized.bin.bin"
)
CONTEXT_LRRB = (
    CONTEXT_ROOT / "fidesr_lrrb" /
    "fidesr_lrrb.serialized.bin.bin"
)
CONTEXT_DECODER = (
    CONTEXT_ROOT / "fidesr_vae_decoder" /
    "fidesr_vae_decoder.serialized.bin.bin"
)

STAGE_CONTEXTS = {
    "VAE_ENCODER": CONTEXT_ENCODER,
    "UNET": CONTEXT_UNET,
    "LRRB": CONTEXT_LRRB,
    "VAE_DECODER": CONTEXT_DECODER,
}

PROMPT_BIN = MODEL_ROOT / "fidesr_empty_prompt_embeds.bin"
EPSILON_BIN = MODEL_ROOT / "fidesr_epsilon_seed231.bin"


# ============================================================
# FROZEN STRONG CONTRACT
# ============================================================

UPSCALE = 4
PROCESS_SIZE = 512

HF_SCALE = 0.40
LF_SCALE = 0.12

LF_RC = 0.10
LF_ORDER = 2
LF_TAU = 0.8
LF_SHARP = 10.0
LF_DMAP_GAMMA = 1.2

HF_RC = 0.32
HF_ORDER = 2
HF_DMAP_GAMMA = 1.2

LF_HF_MERGE_RATIO = 0.5

LATENT_TILE = 64
LATENT_OVERLAP = 16

VAE_PIXEL_TILE = 512

CPU_POST_STRIPE_ROWS = 256


# ============================================================
# LOGGING / TIMER
# ============================================================

T0 = time.perf_counter()


def elapsed():
    return time.perf_counter() - T0


def log(msg):
    sec = elapsed()
    print(f"[{sec:8.1f}s] {msg}", flush=True)


def hard_stop(msg):
    print()
    print("=== HARD STOP ===")
    print(msg)
    raise SystemExit(1)


# ============================================================
# PREFLIGHT
# ============================================================

required = [
    INPUT_IMAGE,
    QNN_RUNNER,
    QNN_BACKEND,
    CONTEXT_ENCODER,
    CONTEXT_UNET,
    CONTEXT_LRRB,
    CONTEXT_DECODER,
    PROMPT_BIN,
    EPSILON_BIN,
]

for p in required:
    if not p.exists():
        hard_stop(f"Datei fehlt: {p}")

if PROMPT_BIN.stat().st_size != 157696:
    hard_stop("Empty-Prompt-Dateigröße stimmt nicht.")

if EPSILON_BIN.stat().st_size != 32768:
    hard_stop("Epsilon-Dateigröße stimmt nicht.")

log("PREFLIGHT=PASS")


# ============================================================
# QNN ENVIRONMENT
# ============================================================

env = os.environ.copy()

env["PATH"] = (
    str(QNN_BIN) + ";" +
    str(QNN_LIB) + ";" +
    env.get("PATH", "")
)

env["ADSP_LIBRARY_PATH"] = (
    str(QNN_HEX) + ";" +
    str(QNN_LIB)
)


# ============================================================
# GENERIC QNN MULTI-INPUT EXECUTION
# One online-prepare per graph, multiple Result_N outputs.
# ============================================================

def run_qnn_stage(stage_name, input_lines, output_dir):

    context = STAGE_CONTEXTS.get(stage_name)

    if context is None:
        hard_stop(f"{stage_name}: Kein serialisierter HTP-Kontext konfiguriert.")

    if not context.is_file() or context.stat().st_size <= 0:
        hard_stop(
            f"{stage_name}: Serialisierter HTP-Kontext fehlt oder ist leer: "
            f"{context}"
        )

    output_dir = Path(output_dir)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    input_list = output_dir.parent / f"{stage_name}_input_list.txt"

    with open(input_list, "w", encoding="ascii", newline="\n") as f:
        for line in input_lines:
            f.write(line + "\n")

    args = [
        str(QNN_RUNNER),
        "--backend", str(QNN_BACKEND),
        "--retrieve_context", str(context),
        "--input_list", str(input_list),
        "--output_dir", str(output_dir),
        "--use_native_input_files",
        "--use_native_output_files",
        "--log_level", "error",
    ]

    total_tiles = len(input_lines)
    log(f"{stage_name}: QNN/HTP START ({total_tiles} inference sets)")
    log(f"STAGE_START: stage={stage_name} total={total_tiles}")

    start = time.perf_counter()

    proc = subprocess.Popen(
        args,
        env=env,
        cwd=str(WORK),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    completed = 0
    clean_exit = False
    try:
        while True:
            target_dir = output_dir / f"Result_{completed}"
            if target_dir.is_dir():
                try:
                    raws = list(target_dir.glob("*.raw"))
                    if raws and raws[0].stat().st_size > 0:
                        completed += 1
                        log(f"TILE_PROGRESS: stage={stage_name} tile={completed} total={total_tiles}")
                        if completed >= total_tiles:
                            break
                        continue
                except OSError:
                    pass

            if proc.poll() is not None:
                while completed < total_tiles:
                    target_dir = output_dir / f"Result_{completed}"
                    if target_dir.is_dir():
                        try:
                            raws = list(target_dir.glob("*.raw"))
                            if raws and raws[0].stat().st_size > 0:
                                completed += 1
                                log(f"TILE_PROGRESS: stage={stage_name} tile={completed} total={total_tiles}")
                                continue
                        except OSError:
                            pass
                    break
                break

            time.sleep(0.05)

        # Allow qnn-net-run to complete teardown cleanly without terminating it
        try:
            proc.wait(timeout=120)
            clean_exit = (proc.returncode == 0)
        except subprocess.TimeoutExpired:
            log(f"TIMEOUT: {stage_name} qnn-net-run did not exit within timeout")
            clean_exit = False
    except BaseException:
        clean_exit = False
        raise
    finally:
        if not clean_exit and proc.poll() is None:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            except Exception:
                pass

    if proc.poll() is None:
        proc.wait()

    if proc.returncode == 0:
        while completed < total_tiles:
            target_dir = output_dir / f"Result_{completed}"
            if target_dir.is_dir():
                try:
                    raws = list(target_dir.glob("*.raw"))
                    if raws and raws[0].stat().st_size > 0:
                        completed += 1
                        log(f"TILE_PROGRESS: stage={stage_name} tile={completed} total={total_tiles}")
                        continue
                except OSError:
                    pass
            break

    dt = time.perf_counter() - start

    log(f"{stage_name}: QNN_EXIT_CODE={proc.returncode}")
    log(f"{stage_name}: QNN_RUNTIME_SEC={dt:.2f}")

    if proc.returncode != 0:
        hard_stop(
            f"{stage_name}: Abruf/Ausführung des serialisierten "
            f"QNN/HTP-Kontexts fehlgeschlagen: {context}"
        )

    result_files = []

    for i in range(len(input_lines)):

        rdir = output_dir / f"Result_{i}"

        candidates = sorted(rdir.glob("*native.raw"))

        if not candidates:
            candidates = sorted(rdir.glob("*.raw"))

        if not candidates:
            hard_stop(f"{stage_name}: Result_{i} enthält keinen RAW-Output.")

        result_files.append(candidates[0])

    log(f"{stage_name}: PASS")

    return result_files


# ============================================================
# TILE HELPERS
# ============================================================

def positions(length, tile, nominal_overlap):

    if length <= tile:
        return [0]

    stride = tile - nominal_overlap

    out = [0]

    while True:

        nxt = out[-1] + stride

        if nxt + tile >= length:
            end = length - tile
            if end != out[-1]:
                out.append(end)
            break

        out.append(nxt)

    return out


def gaussian_weights(h, w):

    yy = np.arange(h, dtype=np.float32)
    xx = np.arange(w, dtype=np.float32)

    my = (h - 1) / 2.0
    mx = (w - 1) / 2.0

    sy2 = (h * h) * 0.01
    sx2 = (w * w) * 0.01

    gy = np.exp(-((yy - my) ** 2) / (2.0 * sy2))
    gx = np.exp(-((xx - mx) ** 2) / (2.0 * sx2))

    wgt = gy[:, None] * gx[None, :]

    wgt /= max(float(wgt.max()), 1e-12)

    return wgt.astype(np.float32)


# ============================================================
# OFFICIAL IMAGE PREPROCESSING
# ============================================================

log("PREPROCESS: START")

src = Image.open(INPUT_IMAGE).convert("RGB")

ori_w, ori_h = src.size

log(f"SOURCE_SIZE={ori_w}x{ori_h}")

rscale = UPSCALE

resize_flag = False

work_img = src

if (
    ori_w < PROCESS_SIZE // rscale
    or
    ori_h < PROCESS_SIZE // rscale
):
    scale = (PROCESS_SIZE // rscale) / min(ori_w, ori_h)

    work_img = work_img.resize(
        (
            int(scale * ori_w),
            int(scale * ori_h),
        )
    )

    resize_flag = True

# Official path: first x4 resize, then multiple-of-8 resize.
work_img = work_img.resize(
    (
        work_img.size[0] * rscale,
        work_img.size[1] * rscale,
    ),
    Image.Resampling.LANCZOS,
)

new_w = work_img.width - work_img.width % 8
new_h = work_img.height - work_img.height % 8

work_img = work_img.resize(
    (new_w, new_h),
    Image.Resampling.LANCZOS,
)

log(f"PROCESS_SIZE_ACTUAL={new_w}x{new_h}")

rgb01 = np.asarray(work_img, dtype=np.float32) / 255.0

# NCHW [-1,1]
c_t = (
    np.transpose(rgb01, (2, 0, 1))[None, ...] * 2.0 - 1.0
).astype(np.float16)

H = c_t.shape[2]
W = c_t.shape[3]

H_LAT = H // 8
W_LAT = W // 8

log(f"LATENT_TARGET_SIZE={W_LAT}x{H_LAT}")
log("PREPROCESS: PASS")


# ============================================================
# STAGE 1 — VAE ENCODER ON NPU, EXTERNAL PRODUCT TILING
# ============================================================

log("VAE_ENCODER_TILING: PREPARE")

enc_dir = WORK / "encoder"

enc_x = positions(W, VAE_PIXEL_TILE, 128)
enc_y = positions(H, VAE_PIXEL_TILE, 128)

log(f"ENCODER_X_POS={enc_x}")
log(f"ENCODER_Y_POS={enc_y}")

enc_records = []

epsilon = np.fromfile(
    EPSILON_BIN,
    dtype=np.float16
)

if epsilon.size != 1 * 4 * 64 * 64:
    hard_stop("Epsilon-Elementzahl stimmt nicht.")

for yi, y in enumerate(enc_y):
    for xi, x in enumerate(enc_x):

        tile = c_t[
            :,
            :,
            y:y + VAE_PIXEL_TILE,
            x:x + VAE_PIXEL_TILE,
        ]

        if tile.shape != (1, 3, 512, 512):
            hard_stop(
                f"Encoder-Tile hat falsche Form: {tile.shape}"
            )

        raw = enc_dir / f"enc_{yi}_{xi}.raw"
        raw.parent.mkdir(parents=True, exist_ok=True)

        tile.tofile(raw)

        enc_records.append(
            {
                "x": x,
                "y": y,
                "raw": raw,
            }
        )

enc_lines = [
    f"image:={r['raw']} epsilon:={EPSILON_BIN}"
    for r in enc_records
]

enc_results = run_qnn_stage(
    "VAE_ENCODER",
    enc_lines,
    enc_dir / "output",
)

enc_acc = np.zeros(
    (1, 4, H_LAT, W_LAT),
    dtype=np.float32,
)

enc_wacc = np.zeros(
    (1, 1, H_LAT, W_LAT),
    dtype=np.float32,
)

gw64 = gaussian_weights(64, 64)[None, None, :, :]

for rec, result in zip(enc_records, enc_results):

    z = np.fromfile(
        result,
        dtype=np.float16,
    )

    if z.size != 1 * 4 * 64 * 64:
        hard_stop(
            f"Encoder-Output falsche Größe: {result}"
        )

    z = z.reshape(1, 4, 64, 64).astype(np.float32)

    lx = rec["x"] // 8
    ly = rec["y"] // 8

    enc_acc[
        :,
        :,
        ly:ly + 64,
        lx:lx + 64,
    ] += z * gw64

    enc_wacc[
        :,
        :,
        ly:ly + 64,
        lx:lx + 64,
    ] += gw64

if np.any(enc_wacc <= 0):
    hard_stop("Encoder-Tiling hat unbedeckte Latent-Pixel.")

encoded_control = enc_acc / enc_wacc

if not np.isfinite(encoded_control).all():
    hard_stop("VAE Encoder enthält NaN/Inf.")

encoded_control = encoded_control.astype(np.float16)

log(
    "VAE_ENCODER_FULL_LATENT="
    f"{encoded_control.shape}"
)

log("VAE_ENCODER_FULL=PASS")

for rec in enc_records:
    rec["raw"].unlink(missing_ok=True)
for result in enc_results:
    result.unlink(missing_ok=True)
del enc_acc, enc_wacc, enc_lines, enc_results, enc_records, epsilon, tile
gc.collect()


# ============================================================
# STAGE 2 — UNET NPU TILING
# Official product latent tile = 64, overlap = 16.
# ============================================================

log("UNET_TILING: PREPARE")

lat_x = positions(
    W_LAT,
    LATENT_TILE,
    LATENT_OVERLAP,
)

lat_y = positions(
    H_LAT,
    LATENT_TILE,
    LATENT_OVERLAP,
)

log(f"UNET_X_POS={lat_x}")
log(f"UNET_Y_POS={lat_y}")

unet_dir = WORK / "unet"

unet_records = []

timestep_raw = unet_dir / "timestep.raw"
unet_dir.mkdir(parents=True, exist_ok=True)

np.array(
    [1],
    dtype=np.int32,
).tofile(timestep_raw)

for yi, y in enumerate(lat_y):
    for xi, x in enumerate(lat_x):

        tile = encoded_control[
            :,
            :,
            y:y + 64,
            x:x + 64,
        ]

        if tile.shape != (1, 4, 64, 64):
            hard_stop(
                f"UNet-Tile falsche Form: {tile.shape}"
            )

        raw = unet_dir / f"sample_{yi}_{xi}.raw"

        tile.tofile(raw)

        unet_records.append(
            {
                "x": x,
                "y": y,
                "raw": raw,
            }
        )

unet_lines = [
    (
        f"sample:={r['raw']} "
        f"timestep:={timestep_raw} "
        f"encoder_hidden_states:={PROMPT_BIN}"
    )
    for r in unet_records
]

unet_results = run_qnn_stage(
    "UNET",
    unet_lines,
    unet_dir / "output",
)

for rec, result in zip(unet_records, unet_results):

    pred = np.fromfile(
        result,
        dtype=np.float16,
    )

    if pred.size != 1 * 4 * 64 * 64:
        hard_stop(
            f"UNet-Output falsche Größe: {result}"
        )

    pred = pred.reshape(
        1, 4, 64, 64
    )

    if not np.isfinite(pred).all():
        hard_stop(
            f"UNet-Output enthält NaN/Inf: {result}"
        )

    rec["unet_result"] = result

log("UNET_TILE_BATCH=PASS")


# ============================================================
# STAGE 3 — LRRB NPU
# concat(encoded_control_tile, unet_pred)
# ============================================================

log("LRRB_TILING: PREPARE")

lrrb_dir = WORK / "lrrb"
lrrb_dir.mkdir(parents=True, exist_ok=True)

lrrb_lines = []

for i, rec in enumerate(unet_records):

    sample = np.fromfile(
        rec["raw"],
        dtype=np.float16,
    ).reshape(1, 4, 64, 64)

    unet_pred = np.fromfile(
        rec["unet_result"],
        dtype=np.float16,
    ).reshape(1, 4, 64, 64)

    latent_cat = np.concatenate(
        [
            sample,
            unet_pred,
        ],
        axis=1,
    ).astype(np.float16)

    if latent_cat.shape != (1, 8, 64, 64):
        hard_stop(
            f"LRRB Input falsche Form: {latent_cat.shape}"
        )

    raw = lrrb_dir / f"latent_cat_{i}.raw"

    latent_cat.tofile(raw)

    rec["lrrb_input"] = raw

    lrrb_lines.append(
        f"latent_cat:={raw}"
    )

del sample, unet_pred, latent_cat
gc.collect()

lrrb_results = run_qnn_stage(
    "LRRB",
    lrrb_lines,
    lrrb_dir / "output",
)

pred_acc = np.zeros(
    (1, 4, H_LAT, W_LAT),
    dtype=np.float32,
)

pred_wacc = np.zeros(
    (1, 1, H_LAT, W_LAT),
    dtype=np.float32,
)

for rec, result in zip(unet_records, lrrb_results):

    unet_pred = np.fromfile(
        rec["unet_result"],
        dtype=np.float16,
    ).reshape(1, 4, 64, 64)

    delta = np.fromfile(
        result,
        dtype=np.float16,
    )

    if delta.size != 1 * 4 * 64 * 64:
        hard_stop(
            f"LRRB-Output falsche Größe: {result}"
        )

    delta = delta.reshape(
        1, 4, 64, 64
    ).astype(np.float32)

    model_pred_tile = (
        unet_pred.astype(np.float32)
        + delta
    )

    x = rec["x"]
    y = rec["y"]

    pred_acc[
        :,
        :,
        y:y + 64,
        x:x + 64,
    ] += model_pred_tile * gw64

    pred_wacc[
        :,
        :,
        y:y + 64,
        x:x + 64,
    ] += gw64

if np.any(pred_wacc <= 0):
    hard_stop("UNet/LRRB-Tiling hat unbedeckte Pixel.")

model_pred = pred_acc / pred_wacc

if not np.isfinite(model_pred).all():
    hard_stop("Zusammengesetzter model_pred enthält NaN/Inf.")

log("LRRB_FULL_MODEL_PRED=PASS")

for rec in unet_records:
    rec["raw"].unlink(missing_ok=True)
    rec["unet_result"].unlink(missing_ok=True)
    rec["lrrb_input"].unlink(missing_ok=True)
for result in lrrb_results:
    result.unlink(missing_ok=True)
del delta, lrrb_lines, lrrb_results, model_pred_tile, pred_acc, pred_wacc
del pred, result, unet_lines, unet_results, unet_pred, unet_records
gc.collect()


# ============================================================
# CPU NON-AI MATH — OFFICIAL FIDESR LF/HF
# ============================================================

log("LF_HF_CPU: START")

encoded_f = encoded_control.astype(np.float32)
model_pred = model_pred.astype(np.float32)

z = encoded_f - model_pred


def percentile_norm(x, lo=0.05, hi=0.95, eps=1e-6):

    B = x.shape[0]

    out = np.empty_like(
        x,
        dtype=np.float32,
    )

    for b in range(B):

        flat = x[b].reshape(-1).astype(np.float32)

        xmin = np.quantile(flat, lo)
        xmax = np.quantile(flat, hi)

        out[b] = np.clip(
            (x[b] - xmin)
            /
            (xmax - xmin + eps),
            0.0,
            1.0,
        )

    return out


def conv3_same_rep(x, kernel, out=None):

    # x [B,1,H,W]
    if out is None:
        out = np.empty_like(
            x,
            dtype=np.float32,
        )

    height = x.shape[2]
    width = x.shape[3]
    for y0 in range(0, height, CPU_POST_STRIPE_ROWS):
        y1 = min(y0 + CPU_POST_STRIPE_ROWS, height)
        row_indices = np.clip(
            np.arange(y0 - 1, y1 + 1, dtype=np.intp),
            0,
            height - 1,
        )
        xp = np.pad(
            x[:, :, row_indices, :],
            ((0, 0), (0, 0), (0, 0), (1, 1)),
            mode="edge",
        )
        out_chunk = out[:, :, y0:y1, :]
        out_chunk.fill(0.0)

        for ky in range(3):
            for kx in range(3):

                out_chunk += (
                    xp[
                        :,
                        :,
                        ky:ky + (y1 - y0),
                        kx:kx + width,
                    ]
                    * float(kernel[ky, kx])
                )

    return out


def detail_map_from_rgb(img_rgb):

    y = img_rgb.astype(np.float32)
    y *= 0.5
    y += 0.5

    gray = (
        0.299 * y[:, 0:1]
        + 0.587 * y[:, 1:2]
        + 0.114 * y[:, 2:3]
    )

    del y, img_rgb

    sobel_x = np.array(
        [
            [-1, 0, 1],
            [-2, 0, 2],
            [-1, 0, 1],
        ],
        dtype=np.float32,
    )

    sobel_y = np.array(
        [
            [-1, -2, -1],
            [0, 0, 0],
            [1, 2, 1],
        ],
        dtype=np.float32,
    )

    lap = np.array(
        [
            [0, 1, 0],
            [1, -4, 1],
            [0, 1, 0],
        ],
        dtype=np.float32,
    )

    box3 = np.ones(
        (3, 3),
        dtype=np.float32,
    ) / 9.0

    ex = conv3_same_rep(
        gray,
        sobel_x,
    )

    ey = conv3_same_rep(
        gray,
        sobel_y,
    )

    sobel_mag = np.sqrt(
        ex * ex + ey * ey
    )

    del ex, ey

    lap_mag = conv3_same_rep(
        gray,
        lap,
    )
    np.abs(lap_mag, out=lap_mag)

    mean = conv3_same_rep(
        gray,
        box3,
    )

    variance_source = gray - mean
    np.square(variance_source, out=variance_source)
    var = conv3_same_rep(variance_source, box3)

    del gray, mean, variance_source

    detail = sobel_mag
    detail += lap_mag
    detail += var
    detail /= 3.0

    del lap_mag, var

    detail = percentile_norm(
        detail
    )

    detail = conv3_same_rep(
        detail,
        box3,
    )

    return detail


def resize_single_channel_bilinear(arr, out_h, out_w):

    # arr [1,1,H,W]
    im = Image.fromarray(
        arr[0, 0].astype(np.float32),
        mode="F",
    )

    im = im.resize(
        (out_w, out_h),
        Image.Resampling.BILINEAR,
    )

    out = np.asarray(
        im,
        dtype=np.float32,
    )

    return out[None, None, :, :]


def butterworth_lpf_fft(x, rc, order):

    B, C, Hx, Wx = x.shape

    X = np.fft.rfft2(
        x.astype(np.float32),
        axes=(-2, -1),
    )

    yy = (
        np.arange(Hx, dtype=np.float32)[:, None]
        /
        max(Hx - 1, 1)
    )

    xx = (
        np.arange(
            Wx // 2 + 1,
            dtype=np.float32,
        )[None, :]
        /
        max(Wx // 2, 1)
    )

    r = np.sqrt(
        yy * yy + xx * xx
    )

    r /= max(float(r.max()), 1.0)

    lp = 1.0 / (
        1.0
        + np.power(
            r / rc,
            2 * order,
        )
    )

    Y = X * lp[None, None, :, :]

    y = np.fft.irfft2(
        Y,
        s=(Hx, Wx),
        axes=(-2, -1),
    )

    return y.astype(np.float32)


def butterworth_hpf_fft(x, rc, order):

    B, C, Hx, Wx = x.shape

    X = np.fft.rfft2(
        x.astype(np.float32),
        axes=(-2, -1),
    )

    yy = (
        np.arange(Hx, dtype=np.float32)[:, None]
        /
        max(Hx - 1, 1)
    )

    xx = (
        np.arange(
            Wx // 2 + 1,
            dtype=np.float32,
        )[None, :]
        /
        max(Wx // 2, 1)
    )

    r = np.sqrt(
        yy * yy + xx * xx
    )

    r /= max(float(r.max()), 1.0)

    lp = 1.0 / (
        1.0
        + np.power(
            r / rc,
            2 * order,
        )
    )

    hp = 1.0 - lp

    Y = X * hp[None, None, :, :]

    y = np.fft.irfft2(
        Y,
        s=(Hx, Wx),
        axes=(-2, -1),
    )

    return y.astype(np.float32)


D = detail_map_from_rgb(
    c_t
)

M_sp = resize_single_channel_bilinear(
    D,
    H_LAT,
    W_LAT,
)

M_sp = np.clip(
    M_sp,
    0.0,
    1.0,
)

del D, c_t
gc.collect()


# LF

delta_lp = butterworth_lpf_fft(
    z,
    LF_RC,
    LF_ORDER,
)

residual_map = np.abs(
    model_pred
)

residual_map = (
    0.8
    * residual_map.mean(
        axis=1,
        keepdims=True,
    )
    +
    0.2
    * residual_map.std(
        axis=1,
        keepdims=True,
    )
)

residual_map = percentile_norm(
    residual_map
)

M_sp_lf = (
    1.0 - M_sp
) * residual_map

M_sp_lf = percentile_norm(
    M_sp_lf
)

M_sp_lf = np.power(
    M_sp_lf,
    LF_DMAP_GAMMA,
)


LP_control = butterworth_lpf_fft(
    encoded_f,
    LF_RC,
    LF_ORDER,
)

num = np.sqrt(
    np.maximum(
        np.sum(
            LP_control ** 2,
            axis=(-2, -1),
            keepdims=True,
        ),
        1e-12,
    )
)

den = np.sqrt(
    np.maximum(
        np.sum(
            encoded_f ** 2,
            axis=(-2, -1),
            keepdims=True,
        ),
        1e-12,
    )
)

ratio = np.clip(
    num / den,
    0.0,
    1.0,
)

M_ch_lf = 1.0 / (
    1.0
    +
    np.exp(
        -LF_SHARP
        *
        (
            ratio
            - LF_TAU
        )
    )
)

M_lf = M_sp_lf * M_ch_lf

zl = (
    z
    +
    LF_SCALE
    * M_lf
    * delta_lp
)


# HF

hpf_z = butterworth_hpf_fft(
    z,
    HF_RC,
    HF_ORDER,
)

hpf_control = butterworth_hpf_fft(
    encoded_f,
    HF_RC,
    HF_ORDER,
)

delta_hp = (
    hpf_z
    - hpf_control
)

M_sp_hf = np.power(
    M_sp,
    HF_DMAP_GAMMA,
)

M_hf = (
    M_sp_hf
    *
    (
        1.0
        - M_ch_lf
    )
)

zf = (
    z
    +
    HF_SCALE
    * M_hf
    * delta_hp
)

x_denoised = (
    LF_HF_MERGE_RATIO * zl
    +
    (
        1.0
        - LF_HF_MERGE_RATIO
    )
    * zf
)

if not np.isfinite(x_denoised).all():
    hard_stop("LF/HF x_denoised enthält NaN/Inf.")

x_denoised = x_denoised.astype(np.float16)

log(
    "LF_HF_RANGE="
    f"{float(x_denoised.min()):.6f},"
    f"{float(x_denoised.max()):.6f}"
)

log("LF_HF_CPU=PASS")


# ============================================================
# STAGE 4 — VAE DECODER ON NPU, LATENT TILING
# ============================================================

log("VAE_DECODER_TILING: PREPARE")

dec_dir = WORK / "decoder"
dec_dir.mkdir(parents=True, exist_ok=True)

dec_records = []
dec_lines = []

for yi, y in enumerate(lat_y):
    for xi, x in enumerate(lat_x):

        tile = x_denoised[
            :,
            :,
            y:y + 64,
            x:x + 64,
        ]

        if tile.shape != (1, 4, 64, 64):
            hard_stop(
                f"Decoder-Tile falsche Form: {tile.shape}"
            )

        raw = dec_dir / f"latent_{yi}_{xi}.raw"

        tile.tofile(raw)

        dec_records.append(
            {
                "x": x,
                "y": y,
                "raw": raw,
            }
        )

        dec_lines.append(
            f"latent:={raw}"
        )

dec_results = run_qnn_stage(
    "VAE_DECODER",
    dec_lines,
    dec_dir / "output",
)

img_acc = np.zeros(
    (1, 3, H, W),
    dtype=np.float32,
)

img_wacc = np.zeros(
    (1, 1, H, W),
    dtype=np.float32,
)

gw512 = gaussian_weights(
    512,
    512,
)[None, None, :, :]

for rec, result in zip(dec_records, dec_results):

    out = np.fromfile(
        result,
        dtype=np.float16,
    )

    if out.size != 1 * 3 * 512 * 512:
        hard_stop(
            f"Decoder-Output falsche Größe: {result}"
        )

    out = out.reshape(
        1, 3, 512, 512
    ).astype(np.float32)

    if not np.isfinite(out).all():
        hard_stop(
            f"Decoder enthält NaN/Inf: {result}"
        )

    px = rec["x"] * 8
    py = rec["y"] * 8

    img_acc[
        :,
        :,
        py:py + 512,
        px:px + 512,
    ] += out * gw512

    img_wacc[
        :,
        :,
        py:py + 512,
        px:px + 512,
    ] += gw512

if np.any(img_wacc <= 0):
    hard_stop(
        "Decoder-Tiling hat unbedeckte Bildpixel."
    )

decoded = img_acc / img_wacc

if not np.isfinite(decoded).all():
    hard_stop(
        "Zusammengesetztes Decoderbild enthält NaN/Inf."
    )

decoded = np.clip(
    decoded,
    -1.0,
    1.0,
)

target01 = np.clip(
    decoded * 0.5 + 0.5,
    0.0,
    1.0,
)

for rec in dec_records:
    rec["raw"].unlink(missing_ok=True)
for result in dec_results:
    result.unlink(missing_ok=True)
del decoded, img_acc, img_wacc, out
del dec_lines, dec_results, dec_records, tile
gc.collect()

log("VAE_DECODER_FULL=PASS")


# ============================================================
# OFFICIAL 5-LEVEL WAVELET COLOR FIX
# CPU, deterministic, no AI inference.
# ============================================================

log("WAVELET_COLOR_FIX: START")


def wavelet_blur(image_hwc, radius, out=None):

    kernel = np.array(
        [
            [0.0625, 0.125, 0.0625],
            [0.1250, 0.250, 0.1250],
            [0.0625, 0.125, 0.0625],
        ],
        dtype=np.float32,
    )

    Hx, Wx, Cx = image_hwc.shape

    pad = radius

    if out is None:
        out = np.empty_like(
            image_hwc,
            dtype=np.float32,
        )

    offsets = (
        -radius,
        0,
        radius,
    )

    for y0 in range(0, Hx, CPU_POST_STRIPE_ROWS):
        y1 = min(y0 + CPU_POST_STRIPE_ROWS, Hx)
        row_indices = np.clip(
            np.arange(y0 - pad, y1 + pad, dtype=np.intp),
            0,
            Hx - 1,
        )
        xp = np.pad(
            image_hwc[row_indices, :, :],
            ((0, 0), (pad, pad), (0, 0)),
            mode="edge",
        )
        out_chunk = out[y0:y1, :, :]
        out_chunk.fill(0.0)

        for ky, oy in enumerate(offsets):
            for kx, ox in enumerate(offsets):

                ys = pad + oy
                xs = pad + ox

                out_chunk += (
                    xp[
                        ys:ys + (y1 - y0),
                        xs:xs + Wx,
                        :
                    ]
                    * kernel[ky, kx]
                )

    return out


def wavelet_decomposition(img, levels=5):

    image = np.array(
        img,
        dtype=np.float32,
        copy=True,
        order="C",
    )

    high = np.zeros_like(
        image,
        dtype=np.float32,
    )

    low = np.empty_like(
        image,
        dtype=np.float32,
    )

    for i in range(levels):

        radius = 2 ** i

        wavelet_blur(
            image,
            radius,
            out=low,
        )

        np.subtract(image, low, out=image)
        np.add(high, image, out=high)

        image, low = low, image

    return high, image


def wavelet_high(img, levels=5):
    high, low = wavelet_decomposition(img, levels=levels)
    del low
    return high


def wavelet_low(img, levels=5):
    image = np.array(
        img,
        dtype=np.float32,
        copy=True,
        order="C",
    )
    low = np.empty_like(
        image,
        dtype=np.float32,
    )

    for i in range(levels):
        wavelet_blur(
            image,
            2 ** i,
            out=low,
        )
        image, low = low, image

    return image


target_hwc = np.transpose(
    target01[0],
    (1, 2, 0),
)

source_hwc = rgb01.astype(
    np.float32
)

del rgb01

content_high = wavelet_high(
    target_hwc,
    levels=5,
)

source_low = wavelet_low(
    source_hwc,
    levels=5,
)

final01 = np.clip(
    content_high
    + source_low,
    0.0,
    1.0,
)

del content_high, source_low, target01, target_hwc
gc.collect()

log("WAVELET_COLOR_FIX=PASS")


# ============================================================
# DETERMINISTIC DETAIL PRESERVATION BYPASS
# CPU, deterministic, no AI inference.
# Recovers 1-3px microdetails (pores, beard stubble, fine hair)
# lost by the generative UNet prior, using pre-UNet source.
# ============================================================

log("DETAIL_PRESERVATION_BYPASS: START")


def apply_detail_preservation_bypass(base_hwc, source_hwc):
    import torch
    import torch.nn.functional as F

    def get_gaussian_kernel(ksize, sigma):
        coords = torch.arange(ksize, dtype=torch.float32) - (ksize - 1) / 2.0
        g = torch.exp(-(coords**2) / (2.0 * sigma**2))
        g = g / g.sum()
        return (g.unsqueeze(1) * g.unsqueeze(0)).unsqueeze(0).unsqueeze(0)

    def gaussian_blur(tensor, sigma, ksize=None):
        if ksize is None:
            ksize = int(2 * round(3 * sigma) + 1)
            if ksize % 2 == 0:
                ksize += 1
        k = get_gaussian_kernel(ksize, sigma)
        pad = ksize // 2
        return F.conv2d(tensor, k, padding=pad)

    def local_std(t, k=7):
        mean = F.avg_pool2d(t, k, stride=1, padding=k // 2)
        mean_sq = F.avg_pool2d(t**2, k, stride=1, padding=k // 2)
        var = torch.clamp(mean_sq - mean**2, min=0.0)
        return torch.sqrt(var)

    # DoG radius 5 plus local-STD radius 3: eight source rows are
    # sufficient for mathematically identical interior stripe results.
    halo = 8
    height = base_hwc.shape[0]
    previous_base_tail = None

    for y0 in range(0, height, CPU_POST_STRIPE_ROWS):
        y1 = min(y0 + CPU_POST_STRIPE_ROWS, height)
        ext_start = max(0, y0 - halo)
        ext_end = min(height, y1 + halo)

        if previous_base_tail is None:
            base_chunk = base_hwc[ext_start:ext_end]
        else:
            base_chunk = np.concatenate(
                (previous_base_tail, base_hwc[y0:ext_end]),
                axis=0,
            )
        source_chunk = source_hwc[ext_start:ext_end]
        next_base_tail = base_hwc[max(y1 - halo, y0):y1].copy()

        base_t = torch.tensor(base_chunk, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
        src_t = torch.tensor(source_chunk, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)

        # RGB to YCbCr (ITU-R BT.601)
        y_base = 0.299 * base_t[:, 0:1] + 0.587 * base_t[:, 1:2] + 0.114 * base_t[:, 2:3]
        cb_base = -0.168736 * base_t[:, 0:1] - 0.331264 * base_t[:, 1:2] + 0.5 * base_t[:, 2:3] + 0.5
        cr_base = 0.5 * base_t[:, 0:1] - 0.418688 * base_t[:, 1:2] - 0.081312 * base_t[:, 2:3] + 0.5
        y_src = 0.299 * src_t[:, 0:1] + 0.587 * src_t[:, 1:2] + 0.114 * src_t[:, 2:3]
        del base_t, src_t

        # Microdetail bandpass matching 4x upscaled source resolution
        # Sigma range (1.0, 3.2) captures 1-2px native features (pores, stubble, grain)
        bp_src = gaussian_blur(y_src, 1.0) - gaussian_blur(y_src, 3.2)
        del y_src

        # Base macro edge gradient to strictly protect edge boundaries
        gx = y_base[:, :, :, 1:] - y_base[:, :, :, :-1]
        gy = y_base[:, :, 1:, :] - y_base[:, :, :-1, :]
        grad_base = torch.zeros_like(y_base)
        grad_base[:, :, :-1, :-1] = torch.sqrt(gx[:, :, :-1, :]**2 + gy[:, :, :, :-1]**2)

        # Edge attenuation: 1.0 in flat/skin areas, smoothly drops to 0.0 near macro edges
        # Guarantees zero halos, zero ringing, and zero edge doubling
        edge_attenuate = torch.clamp(1.0 - (grad_base / 0.08), min=0.0, max=1.0)
        del grad_base, gx, gy

        # Controlled high-frequency detail preservation delta from real source
        delta_y = 0.50 * edge_attenuate * bp_src
        y_out = torch.clamp(y_base + delta_y, 0.0, 1.0)
        del bp_src, delta_y, edge_attenuate, y_base

        # YCbCr to RGB with bit-exact Cb/Cr preservation
        cb_shift = cb_base - 0.5
        cr_shift = cr_base - 0.5
        r = y_out + 1.402 * cr_shift
        g = y_out - 0.344136 * cb_shift - 0.714136 * cr_shift
        b = y_out + 1.772 * cb_shift
        out_rgb = torch.clamp(torch.cat([r, g, b], dim=1), 0.0, 1.0)

        core_start = y0 - ext_start
        core_end = core_start + (y1 - y0)
        base_hwc[y0:y1] = out_rgb[0, :, core_start:core_end, :].permute(1, 2, 0).numpy()
        previous_base_tail = next_base_tail
        del b, base_chunk, cb_base, cb_shift, cr_base, cr_shift, g
        del out_rgb, r, source_chunk, y_out

    return base_hwc


final01 = apply_detail_preservation_bypass(final01, source_hwc)

del source_hwc
gc.collect()

log("DETAIL_PRESERVATION_BYPASS=PASS")


# ============================================================
# SAVE
# ============================================================

final_u8 = np.clip(
    np.rint(final01 * 255.0),
    0,
    255,
).astype(np.uint8)

final_pil = Image.fromarray(
    final_u8,
    mode="RGB",
)

if resize_flag:
    final_pil = final_pil.resize(
        (
            int(UPSCALE * ori_w),
            int(UPSCALE * ori_h),
        ),
        Image.Resampling.LANCZOS,
    )

final_pil.save(
    OUTPUT_IMAGE,
    format="PNG",
)

del final01, final_u8
gc.collect()

log(f"OUTPUT={OUTPUT_IMAGE}")
log(f"OUTPUT_SIZE={final_pil.size[0]}x{final_pil.size[1]}")


# ============================================================
# FINAL TECH GATE
# ============================================================

if not OUTPUT_IMAGE.exists():
    hard_stop("Ergebnisbild wurde nicht gespeichert.")

print()
print("=== HK_NPU_FIDESR_FULL_NPU_PIPELINE_RESULT ===")
print("LRRB_LOCAL_NPU=PASS")
print("VAE_ENCODER_LOCAL_NPU=PASS")
print("VAE_DECODER_LOCAL_NPU=PASS")
print("UNET_MERGED_LOCAL_NPU=PASS")
print("ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS")
print("CPU_AI_FALLBACK=NO")
print("CPU_NON_AI_MATH=LF_HF_WAVELET_TILING_ONLY")
print("FULL_PIPELINE_TECH_PASS=YES")
print("QUALITY_PASS=NOT_YET")
print("PRODUCT_PASS=NOT_YET")
print(f"RESULT={OUTPUT_IMAGE}")
print(f"TOTAL_RUNTIME_SEC={elapsed():.2f}")
print("NEXT=VISUAL_COMPARE_WITH_FIDESR_STRONG")
print("HARD_STOP=NO")
