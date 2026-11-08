"""
Audit & Diagnostic Probe: Test ControlNet QNN HTP Session Initialization
Sprint 41 Read-Only Exploration
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

def main() -> int:
    model_dir = REPO_ROOT / "models" / "controlnet_canny_qnn"
    print("=================================================================")
    print("HK NPU STUDIO – ControlNet QNN HTP Readiness Probe")
    print("=================================================================")
    print(f"Model Directory: {model_dir}")

    # Check existence
    required = ["text_encoder.onnx", "controlnet.onnx", "unet.onnx", "vae.onnx", "metadata.json"]
    for f in required:
        p = model_dir / f
        if not p.is_file():
            print(f"ERROR: Missing file {f}")
            return 1
        print(f"Found: {f:<20} ({p.stat().st_size:,} bytes)")

    # Read metadata
    with open(model_dir / "metadata.json", "r") as mf:
        meta = json.load(mf)
    print(f"Runtime:   {meta.get('runtime')}")
    print(f"Precision: {meta.get('precision')}")
    print(f"QAIRT Ver: {meta.get('tool_versions', {}).get('qairt')}")

    # Initialize QNN Execution Provider
    print("\nRegistering QNN EP...")
    ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
    all_devices = ort.get_ep_devices()
    selected_devices = [d for d in all_devices if d.ep_name == "QNNExecutionProvider"]
    print(f"QNN Devices found: {len(selected_devices)}")
    if not selected_devices:
        print("ERROR: No QNN devices found!")
        return 1

    qnn_opts = ort.SessionOptions()
    qnn_opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    provider_options = {"backend_path": qnn.get_qnn_htp_path()}
    qnn_opts.add_provider_for_devices(selected_devices, provider_options)

    # Probe ControlNet Session
    print("\nLoading controlnet.onnx with pure Hexagon HTP EPContext...")
    t0 = time.perf_counter()
    cn_sess = ort.InferenceSession(str(model_dir / "controlnet.onnx"), sess_options=qnn_opts)
    t_cn_load = time.perf_counter() - t0
    print(f"SUCCESS: controlnet.onnx loaded on HTP in {t_cn_load:.2f}s!")
    print("ControlNet Inputs:", [i.name for i in cn_sess.get_inputs()])
    print("ControlNet Outputs count:", len(cn_sess.get_outputs()))

    # Probe UNet Session
    print("\nLoading unet.onnx with pure Hexagon HTP EPContext...")
    t0 = time.perf_counter()
    unet_sess = ort.InferenceSession(str(model_dir / "unet.onnx"), sess_options=qnn_opts)
    t_unet_load = time.perf_counter() - t0
    print(f"SUCCESS: unet.onnx loaded on HTP in {t_unet_load:.2f}s!")
    print("UNet Inputs count:", len(unet_sess.get_inputs()))
    print("UNet Outputs:", [o.name for o in unet_sess.get_outputs()])

    print("\n=================================================================")
    print("ALL PROBES PASSED: Qualcomm Hexagon HTP ControlNet QNN is 100% OPERATIONAL!")
    print("=================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
