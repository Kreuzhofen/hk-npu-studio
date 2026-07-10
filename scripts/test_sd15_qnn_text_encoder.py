#!/usr/bin/env python3
"""Strict QNN/HTP smoke test for the Qualcomm SD 1.5 text encoder wrapper."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import logging
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_MODEL_DIR = Path(
    r"C:\SnapdragonAI\temp\stable_diffusion_v1_5_qnn_inspection"
    r"\stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite"
)
DEFAULT_OUTPUT_DIR = Path(os.environ.get("TEMP", ".")) / "SnapdragonAI_SD15_QNN_TextEncoder"
AI_STACK_ROOT = Path(r"C:\Qualcomm\AIStack\2.47.0.260601")
QNN_PROVIDER_DIR = Path(
    r"C:\Users\holge\AppData\Roaming\Python\Python311-arm64"
    r"\site-packages\onnxruntime_qnn"
)
SKELETON_DIR = AI_STACK_ROOT / "lib" / "hexagon-v73" / "unsigned"
EXPECTED_CONTEXT_REF = "./text_encoder_qairt_context.bin"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Strict QNN SD1.5 text encoder diagnostic.")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR))
    parser.add_argument("--prompt", default="A red sports car")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--profile", action="store_true")
    return parser.parse_args()


def setup_logging(output_dir: Path, verbose: bool) -> logging.Logger:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("sd15_qnn_text_encoder")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(output_dir / "runtime.log", mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def write_result(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "result.json"
    with result_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)


def base_result(args: argparse.Namespace, model_dir: Path, output_dir: Path) -> dict[str, Any]:
    return {
        "status": "error",
        "prompt": args.prompt,
        "model_path": str(model_dir / "text_encoder.onnx"),
        "context_binary_path": str(model_dir / "text_encoder_qairt_context.bin"),
        "context_binary_reference": None,
        "provider": "QNNExecutionProvider",
        "cpu_fallback_disabled": True,
        "htp_version": 73,
        "session_created": False,
        "session_providers": [],
        "inference_completed": False,
        "output_name": "text_embedding",
        "output_shape": None,
        "output_dtype": None,
        "statistics": None,
        "npu_verified": False,
        "profile_files": [],
        "runtime": {},
        "tokenizer": {
            "implementation": "deterministic_dummy_tokens",
            "prompt_semantics": "runtime_test_without_verified_prompt_semantics",
            "input_shape": [1, 77],
            "input_dtype": "int32",
        },
        "output_dir": str(output_dir),
        "error": None,
    }


def fail(result: dict[str, Any], output_dir: Path, logger: logging.Logger, message: str) -> int:
    logger.error(message)
    result["status"] = "error"
    result["error"] = message
    result["profile_files"] = collect_profile_files(output_dir)
    write_result(output_dir, result)
    return 1


def import_qnn_runtime(logger: logging.Logger) -> tuple[Any, Any]:
    add_process_path(QNN_PROVIDER_DIR, logger)
    add_process_path(AI_STACK_ROOT / "bin" / "aarch64-windows-msvc", logger)
    add_process_path(AI_STACK_ROOT / "lib" / "aarch64-windows-msvc", logger)
    os.environ["ADSP_LIBRARY_PATH"] = str(SKELETON_DIR)

    import onnxruntime as ort
    import onnxruntime_qnn

    try:
        ort.register_execution_provider_library(
            onnxruntime_qnn.get_ep_name(),
            onnxruntime_qnn.get_library_path(),
        )
    except Exception as exc:
        message = str(exc)
        if "already registered" not in message.lower():
            raise
        logger.debug("QNN provider was already registered: %s", exc)

    return ort, onnxruntime_qnn


def add_process_path(path: Path, logger: logging.Logger) -> None:
    if not path.exists():
        logger.debug("Skipping missing runtime path: %s", path)
        return
    path_text = str(path)
    os.environ["PATH"] = path_text + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(path_text)
        except Exception as exc:
            logger.debug("add_dll_directory skipped for %s: %s", path, exc)


def load_metadata(model_dir: Path) -> dict[str, Any]:
    metadata_path = model_dir / "metadata.json"
    with metadata_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_files(model_dir: Path) -> None:
    required = [
        model_dir / "metadata.json",
        model_dir / "text_encoder.onnx",
        model_dir / "text_encoder_qairt_context.bin",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("Missing required file(s): " + ", ".join(missing))


def validate_metadata(metadata: dict[str, Any]) -> None:
    htp_version = metadata.get("chipset_attributes", {}).get("htp_version")
    if htp_version != 73:
        raise RuntimeError(f"metadata htp_version mismatch: {htp_version!r}")

    text_encoder = metadata.get("model_files", {}).get("text_encoder.onnx", {})
    tokens = text_encoder.get("inputs", {}).get("tokens")
    embedding = text_encoder.get("outputs", {}).get("text_embedding")
    if tokens != {"shape": [1, 77], "dtype": "int32"}:
        raise RuntimeError(f"metadata tokens contract mismatch: {tokens!r}")
    if not embedding:
        raise RuntimeError("metadata output text_embedding is missing")
    if embedding.get("shape") != [1, 77, 768]:
        raise RuntimeError(f"metadata output shape mismatch: {embedding.get('shape')!r}")


def validate_wrapper_reference(model_path: Path, context_path: Path) -> str:
    data = model_path.read_bytes()
    marker = EXPECTED_CONTEXT_REF.encode("utf-8")
    if marker not in data:
        raise RuntimeError(f"ONNX EPContext wrapper does not reference {EXPECTED_CONTEXT_REF}")
    if not context_path.is_file():
        raise RuntimeError(f"Context binary missing: {context_path}")
    return EXPECTED_CONTEXT_REF


def validate_session_contract(session: Any) -> None:
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if len(inputs) != 1:
        raise RuntimeError(f"expected exactly one input, got {len(inputs)}")
    if len(outputs) != 1:
        raise RuntimeError(f"expected exactly one output, got {len(outputs)}")

    input_meta = inputs[0]
    output_meta = outputs[0]
    if input_meta.name != "tokens":
        raise RuntimeError(f"input name mismatch: {input_meta.name!r}")
    if input_meta.type != "tensor(int32)":
        raise RuntimeError(f"input dtype mismatch: {input_meta.type!r}")
    if list(input_meta.shape) != [1, 77]:
        raise RuntimeError(f"input shape mismatch: {input_meta.shape!r}")
    if output_meta.name != "text_embedding":
        raise RuntimeError(f"output name mismatch: {output_meta.name!r}")
    if list(output_meta.shape) != [1, 77, 768]:
        raise RuntimeError(f"output shape mismatch: {output_meta.shape!r}")


def build_dummy_tokens(prompt: str) -> np.ndarray:
    del prompt
    tokens = np.zeros((1, 77), dtype=np.int32)
    tokens[0, 0] = 49406
    tokens[0, 1] = 320
    tokens[0, 2] = 736
    tokens[0, 3] = 2522
    tokens[0, 4] = 1615
    tokens[0, 5] = 49407
    return tokens


def output_stats(array: np.ndarray) -> dict[str, Any]:
    as_float = array.astype(np.float32)
    return {
        "min": float(as_float.min()),
        "max": float(as_float.max()),
        "mean": float(as_float.mean()),
        "std": float(as_float.std()),
        "nan_count": int(np.isnan(as_float).sum()),
        "inf_count": int(np.isinf(as_float).sum()),
        "all_zero": bool(np.all(as_float == 0.0)),
    }


def collect_profile_files(output_dir: Path) -> list[str]:
    return sorted(str(path) for path in output_dir.glob("onnx_profile_*.json"))


def has_htp_profile_evidence(profile_files: list[str], logger: logging.Logger) -> bool:
    needles = ("QNNExecutionProvider", "QNNContext", "EPContext", "text_encoder_qairt_context")
    for profile in profile_files:
        try:
            text = Path(profile).read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            logger.debug("Failed to read profile %s: %s", profile, exc)
            continue
        if any(needle in text for needle in needles):
            return True
    return False


def main() -> int:
    args = parse_args()
    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)
    logger = setup_logging(output_dir, args.verbose)
    result = base_result(args, model_dir, output_dir)

    logger.info("Starting strict SD1.5 QNN text encoder diagnostic")
    logger.info("Model dir: %s", model_dir)
    logger.info("Output dir: %s", output_dir)

    try:
        validate_files(model_dir)
        context_ref = validate_wrapper_reference(
            model_dir / "text_encoder.onnx",
            model_dir / "text_encoder_qairt_context.bin",
        )
        result["context_binary_reference"] = context_ref

        metadata = load_metadata(model_dir)
        validate_metadata(metadata)
        ort, onnxruntime_qnn = import_qnn_runtime(logger)

        result["runtime"] = {
            "python_version": sys.version,
            "python_machine": platform.machine(),
            "onnxruntime_version": ort.__version__,
            "available_providers": list(ort.get_available_providers()),
            "qnn_provider_path": str(Path(onnxruntime_qnn.get_library_path()).parent),
            "qnn_provider_library": onnxruntime_qnn.get_library_path(),
            "backend_path": onnxruntime_qnn.get_qnn_htp_path(),
            "skeleton_path": str(SKELETON_DIR),
            "ai_stack_root": str(AI_STACK_ROOT),
            "metadata_qairt_version": metadata.get("tool_versions", {}).get("qairt"),
            "metadata_onnxruntime_version": metadata.get("tool_versions", {}).get("onnx_runtime"),
            "provider_options": {},
        }

        if platform.machine().upper() != "ARM64":
            raise RuntimeError(f"Python process is not ARM64: {platform.machine()}")
        if "QNNExecutionProvider" not in result["runtime"]["available_providers"]:
            raise RuntimeError("QNNExecutionProvider is not available after registration")
        if not SKELETON_DIR.is_dir():
            raise RuntimeError(f"V73 skeleton path missing: {SKELETON_DIR}")

        session_options = ort.SessionOptions()
        session_options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        if args.profile:
            session_options.enable_profiling = True
            session_options.profile_file_prefix = str(output_dir / "onnx_profile")

        provider_options = {
            "backend_path": onnxruntime_qnn.get_qnn_htp_path(),
        }
        result["runtime"]["provider_options"] = dict(provider_options)

        logger.info("Creating strict QNN session with provider options: %s", provider_options)
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        start_create = time.perf_counter()
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            session = ort.InferenceSession(
                str(model_dir / "text_encoder.onnx"),
                sess_options=session_options,
                providers=["QNNExecutionProvider"],
                provider_options=[provider_options],
            )
        create_ms = (time.perf_counter() - start_create) * 1000.0
        qnn_logs = stdout_capture.getvalue() + stderr_capture.getvalue()
        if qnn_logs.strip():
            logger.info("Captured ORT/QNN session output:\n%s", qnn_logs.strip())

        result["session_created"] = True
        result["session_providers"] = list(session.get_providers())
        result["session_creation_ms"] = create_ms
        validate_session_contract(session)

        if result["session_providers"] != ["QNNExecutionProvider"]:
            raise RuntimeError(f"unexpected session providers: {result['session_providers']!r}")

        tokens = build_dummy_tokens(args.prompt)
        logger.info("Using deterministic dummy tokens; prompt semantics are not fully verified")

        start_inference = time.perf_counter()
        outputs = session.run(["text_embedding"], {"tokens": tokens})
        inference_ms = (time.perf_counter() - start_inference) * 1000.0
        output = outputs[0]
        stats = output_stats(output)
        profile_path = session.end_profiling() if args.profile else ""
        if profile_path:
            logger.info("ORT profile written: %s", profile_path)

        result["inference_completed"] = True
        result["output_name"] = "text_embedding"
        result["output_shape"] = list(output.shape)
        result["output_dtype"] = str(output.dtype)
        result["statistics"] = stats | {"inference_ms": inference_ms}
        result["profile_files"] = collect_profile_files(output_dir)

        if result["output_shape"] != [1, 77, 768]:
            raise RuntimeError(f"output shape mismatch: {result['output_shape']!r}")
        if stats["nan_count"] or stats["inf_count"]:
            raise RuntimeError(f"invalid output values: NaN={stats['nan_count']} Inf={stats['inf_count']}")
        if stats["all_zero"]:
            raise RuntimeError("output tensor is fully zero")

        htp_evidence = (
            result["session_providers"] == ["QNNExecutionProvider"]
            and result["inference_completed"]
            and context_ref == EXPECTED_CONTEXT_REF
            and (has_htp_profile_evidence(result["profile_files"], logger) or "QNNContext" in qnn_logs)
        )
        result["npu_verified"] = bool(htp_evidence)
        result["status"] = "success" if result["npu_verified"] else "error"
        if not result["npu_verified"]:
            result["error"] = "Inference completed, but profiling/logs did not provide sufficient HTP evidence"
            logger.error(result["error"])
            write_result(output_dir, result)
            return 2

        logger.info("Strict QNN/HTP text encoder test completed successfully")
        write_result(output_dir, result)
        return 0
    except Exception as exc:
        return fail(result, output_dir, logger, str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
