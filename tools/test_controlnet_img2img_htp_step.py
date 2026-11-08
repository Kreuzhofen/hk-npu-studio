"""
Verify single step of ControlNet Canny on Qualcomm Hexagon HTP
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Ensure repo root on sys.path
REPO_ROOT = Path(r"C:\SnapdragonAI")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import onnxruntime as ort
import onnxruntime_qnn as qnn
from engine.controlnet_canny_backend import canny_edge_detector

def main() -> int:
    model_dir = REPO_ROOT / "models" / "controlnet_canny_qnn"
    with open(model_dir / "metadata.json") as f:
        meta = json.load(f)["model_files"]

    ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
    devices = [d for d in ort.get_ep_devices() if d.ep_name == "QNNExecutionProvider"]
    qnn_opts = ort.SessionOptions()
    qnn_opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    qnn_opts.add_provider_for_devices(devices, {"backend_path": qnn.get_qnn_htp_path()})

    print("Loading controlnet and unet sessions on HTP...")
    cn_sess = ort.InferenceSession(str(model_dir / "controlnet.onnx"), sess_options=qnn_opts)
    unet_sess = ort.InferenceSession(str(model_dir / "unet.onnx"), sess_options=qnn_opts)
    print("Sessions loaded.")

    # Dummy inputs
    lat_arr = np.zeros((1, 64, 64, 4), dtype=np.float32)
    t_val = 601
    cfg_scale = 7.5

    # Quantize for CN
    p_lat_cn = meta["controlnet.onnx"]["inputs"]["latent"]["quantization_parameters"]
    lat_q_cn = np.clip(np.round(lat_arr / p_lat_cn["scale"]) + p_lat_cn["zero_point"], 0, 65535).astype(np.uint16)

    p_t_cn = meta["controlnet.onnx"]["inputs"]["timestep"]["quantization_parameters"]
    t_q_cn = np.clip(np.round(t_val / p_t_cn["scale"]) + p_t_cn["zero_point"], 0, 65535).astype(np.uint16)
    t_arr_cn = np.array([[t_q_cn]], dtype=np.uint16)

    p_txt_cn = meta["controlnet.onnx"]["inputs"]["text_emb"]["quantization_parameters"]
    txt_arr = np.zeros((1, 77, 768), dtype=np.float32)
    txt_q_cn = np.clip(np.round(txt_arr / p_txt_cn["scale"]) + p_txt_cn["zero_point"], 0, 65535).astype(np.uint16)

    canny = np.zeros((1, 512, 512, 3), dtype=np.uint16)

    print("Running controlnet.onnx on Hexagon HTP...")
    t0 = time.perf_counter()
    cn_outs = cn_sess.run(None, {
        "latent": lat_q_cn,
        "timestep": t_arr_cn,
        "text_emb": txt_q_cn,
        "image_cond": canny,
    })
    t_cn = (time.perf_counter() - t0) * 1000.0
    print(f"ControlNet run success in {t_cn:.2f} ms! Outputs: {len(cn_outs)}")

    # Format UNet inputs
    p_lat_u = meta["unet.onnx"]["inputs"]["latent"]["quantization_parameters"]
    lat_q_u = np.clip(np.round(lat_arr / p_lat_u["scale"]) + p_lat_u["zero_point"], 0, 65535).astype(np.uint16)

    p_t_u = meta["unet.onnx"]["inputs"]["timestep"]["quantization_parameters"]
    t_q_u = np.clip(np.round(t_val / p_t_u["scale"]) + p_t_u["zero_point"], 0, 65535).astype(np.uint16)
    t_arr_u = np.array([[t_q_u]], dtype=np.uint16)

    p_txt_u = meta["unet.onnx"]["inputs"]["text_emb"]["quantization_parameters"]
    txt_q_u = np.clip(np.round(txt_arr / p_txt_u["scale"]) + p_txt_u["zero_point"], 0, 65535).astype(np.uint16)

    unet_in = {
        "latent": lat_q_u,
        "timestep": t_arr_u,
        "text_emb": txt_q_u,
    }

    # Map CN outputs to UNet inputs with scaling factor
    factor = 0.75
    out_names = [o.name for o in cn_sess.get_outputs()]
    cn_dict = dict(zip(out_names, cn_outs))

    for i in range(12):
        c_name = f"down_block_{i}"
        u_name = f"controlnet_downblock{i}"
        p_c = meta["controlnet.onnx"]["outputs"][c_name]["quantization_parameters"]
        p_u = meta["unet.onnx"]["inputs"][u_name]["quantization_parameters"]
        # Dequantize
        f_val = (cn_dict[c_name].astype(np.float32) - p_c["zero_point"]) * p_c["scale"] * factor
        q_val = np.clip(np.round(f_val / p_u["scale"]) + p_u["zero_point"], 0, 65535).astype(np.uint16)
        unet_in[u_name] = q_val

    p_cm = meta["controlnet.onnx"]["outputs"]["mid_block"]["quantization_parameters"]
    p_um = meta["unet.onnx"]["inputs"]["controlnet_midblock"]["quantization_parameters"]
    f_mid = (cn_dict["mid_block"].astype(np.float32) - p_cm["zero_point"]) * p_cm["scale"] * factor
    unet_in["controlnet_midblock"] = np.clip(np.round(f_mid / p_um["scale"]) + p_um["zero_point"], 0, 65535).astype(np.uint16)

    print("Running unet.onnx on Hexagon HTP...")
    t0 = time.perf_counter()
    out_lat = unet_sess.run(["output_latent"], unet_in)[0]
    t_u = (time.perf_counter() - t0) * 1000.0
    print(f"UNet run success in {t_u:.2f} ms! Output shape: {out_lat.shape}, dtype: {out_lat.dtype}")
    print("ALL TESTS PASSED: Combined ControlNet + UNet pipeline runs seamlessly on Qualcomm Hexagon HTP!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
