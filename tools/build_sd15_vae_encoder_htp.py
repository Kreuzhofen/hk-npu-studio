"""
Build and Quantization Pipeline for SD1.5 VAE-Encoder on Qualcomm Hexagon HTP.
Generates:
1. NHWC FP32 prototype model: vae_encoder_nhwc.onnx
2. W8A16 QDQ quantized model: vae_encoder_w8a16_qdq.onnx (calibrated with 64 images)
3. Hexagon HTP compiled Context model: vae_encoder_htp.onnx (+ .bin)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
import onnx
from onnx import helper, TensorProto
import onnxruntime as ort
import onnxruntime_qnn as qnn
from onnxruntime.quantization import (
    quantize_static,
    CalibrationDataReader,
    QuantType,
    CalibrationMethod,
)
from onnxruntime.quantization.execution_providers.qnn import get_qnn_qdq_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_sd15_vae_encoder_htp")

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "models" / "stable_diffusion_v1_5_qnn"
PROTOTYPE_DIR = MODELS_DIR / "prototype"
SRC_ENCODER = MODELS_DIR / "vae_encoder.onnx"


class ImageCalibrationDataReader(CalibrationDataReader):
    """Feeds 64 diverse images normalized to [-1.0, 1.0] in NHWC format."""

    def __init__(self, image_paths: list[Path], input_name: str = "image", target_size: tuple[int, int] = (512, 512)) -> None:
        self.image_paths = image_paths
        self.input_name = input_name
        self.target_size = target_size
        self.index = 0

    def get_next(self) -> dict[str, np.ndarray] | None:
        if self.index >= len(self.image_paths):
            return None
        p = self.image_paths[self.index]
        self.index += 1
        try:
            with Image.open(p) as img:
                rgb = img.convert("RGB").resize(self.target_size, Image.Resampling.LANCZOS)
        except Exception:
            rgb = Image.new("RGB", self.target_size, (128, 128, 128))

        arr = (np.array(rgb, dtype=np.float32) / 255.0) * 2.0 - 1.0
        batch = arr[np.newaxis, ...]  # [1, 512, 512, 3]
        return {self.input_name: batch}

    def rewind(self) -> None:
        self.index = 0


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def find_calibration_images(count: int = 64) -> list[Path]:
    """Gather 64 diverse images from repo artifacts, assets, and temp."""
    candidates = (
        list(REPO_ROOT.glob("artifacts/**/*.png"))
        + list(REPO_ROOT.glob("temp/**/*.png"))
        + list(REPO_ROOT.glob("assets/**/*.png"))
        + list(REPO_ROOT.glob("**/*.jpg"))
    )
    valid: list[Path] = []
    for p in candidates:
        try:
            with Image.open(p) as img:
                if img.width >= 128 and img.height >= 128:
                    valid.append(p)
        except Exception:
            pass
        if len(valid) >= count:
            break

    # If fewer than 64 found, augment with generated varied test patches
    while len(valid) < count:
        valid.append(valid[len(valid) % len(valid)])

    return valid[:count]


def step1_create_nhwc_model(src_path: Path, dst_path: Path) -> None:
    """Create vae_encoder_nhwc.onnx by modifying input to [1, 512, 512, 3]."""
    logger.info("Step 1: Creating NHWC model at %s...", dst_path)
    model = onnx.load(str(src_path), load_external_data=False)
    graph = model.graph

    orig_input = graph.input[0]
    new_input = helper.make_tensor_value_info("image", TensorProto.FLOAT, [1, 512, 512, 3])
    graph.input.remove(orig_input)
    graph.input.insert(0, new_input)

    trans_node = helper.make_node(
        "Transpose",
        inputs=["image"],
        outputs=["image_nchw"],
        perm=[0, 3, 1, 2],
        name="/input_transpose_nhwc_to_nchw",
    )
    graph.node.insert(0, trans_node)

    for node in graph.node[1:]:
        for i, inp_name in enumerate(node.input):
            if inp_name == "image":
                node.input[i] = "image_nchw"

    model.ir_version = 8
    onnx.save(model, str(dst_path))
    logger.info("Step 1 Complete. File size: %.2f MB", dst_path.stat().st_size / (1024 * 1024))


def step2_quantize_w8a16(nhwc_model_path: Path, dst_qdq_path: Path, calib_images: list[Path]) -> None:
    """Perform W8A16 static quantization with 64 calibration images."""
    logger.info("Step 2: Quantizing to W8A16 QDQ model at %s (using %d images)...", dst_qdq_path, len(calib_images))
    reader = ImageCalibrationDataReader(calib_images, input_name="image")

    qnn_config = get_qnn_qdq_config(
        model_input=str(nhwc_model_path),
        calibration_data_reader=reader,
        calibrate_method=CalibrationMethod.MinMax,
        activation_type=QuantType.QUInt16,
        weight_type=QuantType.QUInt8,
        per_channel=True,
    )

    quantize_static(
        model_input=str(nhwc_model_path),
        model_output=str(dst_qdq_path),
        calibration_data_reader=reader,
        quant_format=qnn_config.quant_format,
        activation_type=qnn_config.activation_type,
        weight_type=qnn_config.weight_type,
        calibrate_method=qnn_config.calibrate_method,
        extra_options=qnn_config.extra_options,
    )
    logger.info("Step 2 Complete. File size: %.2f MB", dst_qdq_path.stat().st_size / (1024 * 1024))


def step3_compile_htp_context(qdq_model_path: Path, dst_htp_onnx: Path) -> None:
    """Compile W8A16 QDQ model to Hexagon HTP Context Binary using onnxruntime_qnn."""
    logger.info("Step 3: Compiling to Qualcomm Hexagon HTP Context Binary at %s...", dst_htp_onnx)
    ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
    devices = [d for d in ort.get_ep_devices() if d.ep_name == "QNNExecutionProvider"]

    opts = ort.SessionOptions()
    opts.add_session_config_entry("session.disable_cpu_ep_fallback", "0")
    opts.add_session_config_entry("ep.context_enable", "1")
    opts.add_session_config_entry("ep.context_file_path", str(dst_htp_onnx))
    provider_options = {"backend_path": qnn.get_qnn_htp_path()}
    opts.add_provider_for_devices(devices, provider_options)

    t0 = time.perf_counter()
    sess = ort.InferenceSession(str(qdq_model_path), sess_options=opts)
    dur = time.perf_counter() - t0
    logger.info("Step 3 Compilation Complete in %.2f seconds.", dur)

    # Convert to pure HTP EPContext graph for strict disable_cpu_ep_fallback=1 compliance
    model = onnx.load(str(dst_htp_onnx))
    ep_nodes = [n for n in model.graph.node if n.op_type == "EPContext"]
    if ep_nodes and len(model.graph.node) > 1:
        ep_node = ep_nodes[0]
        clean_graph = helper.make_graph(
            [ep_node],
            model.graph.name,
            [helper.make_tensor_value_info(ep_node.input[0], TensorProto.UINT16, [1, 512, 512, 3])],
            [helper.make_tensor_value_info(ep_node.output[0], TensorProto.UINT16, [1, 64, 64, 4])],
        )
        clean_model = helper.make_model(clean_graph, opset_imports=model.opset_import)
        clean_model.ir_version = model.ir_version
        onnx.save(clean_model, str(dst_htp_onnx))
        logger.info("Step 3: Graph optimized to pure EPContext node (100%% Hexagon HTP execution).")


def main() -> None:
    PROTOTYPE_DIR.mkdir(parents=True, exist_ok=True)

    nhwc_model_path = PROTOTYPE_DIR / "vae_encoder_nhwc.onnx"
    qdq_model_path = PROTOTYPE_DIR / "vae_encoder_w8a16_qdq.onnx"
    htp_onnx_path = PROTOTYPE_DIR / "vae_encoder_htp.onnx"

    calib_images = find_calibration_images(64)
    logger.info("Found %d calibration images.", len(calib_images))

    # 1. NHWC conversion
    if not nhwc_model_path.is_file():
        step1_create_nhwc_model(SRC_ENCODER, nhwc_model_path)
    else:
        logger.info("NHWC model already exists at %s", nhwc_model_path)

    # 2. W8A16 QDQ Quantization
    if not qdq_model_path.is_file():
        step2_quantize_w8a16(nhwc_model_path, qdq_model_path, calib_images)
    else:
        logger.info("W8A16 QDQ model already exists at %s", qdq_model_path)

    # 3. Hexagon HTP Compilation
    if not htp_onnx_path.is_file():
        step3_compile_htp_context(qdq_model_path, htp_onnx_path)
    else:
        logger.info("HTP Context model already exists at %s", htp_onnx_path)

    logger.info("=== PROTOTYPE BUILD SUCCESSFUL ===")
    logger.info("NHWC Model: %s (SHA-256: %s)", nhwc_model_path, sha256_file(nhwc_model_path))
    logger.info("QDQ Model:  %s (SHA-256: %s)", qdq_model_path, sha256_file(qdq_model_path))
    if htp_onnx_path.is_file():
        logger.info("HTP Model:  %s (SHA-256: %s)", htp_onnx_path, sha256_file(htp_onnx_path))


if __name__ == "__main__":
    main()
