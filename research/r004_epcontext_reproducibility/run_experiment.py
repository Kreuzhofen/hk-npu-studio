from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import onnxruntime_qnn as ort_qnn


EXPERIMENT_DIR = Path(__file__).resolve().parent
REPOSITORY_DIR = EXPERIMENT_DIR.parents[1]
LOCAL_ONNX_SITE_PACKAGES = (
    REPOSITORY_DIR / "temp" / "sd21_wrapper_venv" / "Lib" / "site-packages"
)
if str(LOCAL_ONNX_SITE_PACKAGES) not in sys.path:
    sys.path.append(str(LOCAL_ONNX_SITE_PACKAGES))

import onnx  # noqa: E402
from onnx import TensorProto, helper, numpy_helper  # noqa: E402


MODEL_PATH = EXPERIMENT_DIR / "minimal_qdq_conv.onnx"
INPUT_PATH = EXPERIMENT_DIR / "test_input.npy"
CPU_OUTPUT_PATH = EXPERIMENT_DIR / "cpu_reference_output.npy"
BUILD_NAMES = ("build_a", "build_b")
WRAPPER_NAME = "minimal_qdq_conv_ctx.onnx"
QNN_BACKEND_PATH = Path(ort_qnn.get_qnn_htp_path()).resolve()
QNN_PROVIDER_LIBRARY_PATH = Path(ort_qnn.get_library_path()).resolve()
EXPECTED_ORT_VERSION = "1.27.0"
EXPECTED_QNN_PACKAGE_VERSION = "2.3.0"
OUTPUT_QUANTIZATION_SCALE = 0.08


class ExperimentAbort(RuntimeError):
    """Raised when a mandatory R-004 acceptance condition is not met."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")


def save_npy_exclusive(path: Path, value: np.ndarray) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    with path.open("xb") as stream:
        np.save(stream, value, allow_pickle=False)


def make_test_model(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")

    input_info = helper.make_tensor_value_info("input", TensorProto.UINT8, [1, 1, 4, 4])
    output_info = helper.make_tensor_value_info("output", TensorProto.UINT8, [1, 1, 4, 4])

    x_scale = np.asarray(0.05, dtype=np.float32)
    x_zero_point = np.asarray(128, dtype=np.uint8)
    weight_scale = np.asarray(0.04, dtype=np.float32)
    weight_zero_point = np.asarray(0, dtype=np.int8)
    output_scale = np.asarray(OUTPUT_QUANTIZATION_SCALE, dtype=np.float32)
    output_zero_point = np.asarray(120, dtype=np.uint8)
    quantized_weight = np.asarray(
        [[[[1, -2, 3], [-1, 2, -3], [1, 0, -1]]]],
        dtype=np.int8,
    )
    bias_scale = np.asarray(float(x_scale * weight_scale), dtype=np.float32)
    bias_zero_point = np.asarray(0, dtype=np.int32)
    quantized_bias = np.asarray([5], dtype=np.int32)

    initializers = [
        numpy_helper.from_array(x_scale, "x_scale"),
        numpy_helper.from_array(x_zero_point, "x_zero_point"),
        numpy_helper.from_array(weight_scale, "weight_scale"),
        numpy_helper.from_array(weight_zero_point, "weight_zero_point"),
        numpy_helper.from_array(output_scale, "output_scale"),
        numpy_helper.from_array(output_zero_point, "output_zero_point"),
        numpy_helper.from_array(quantized_weight, "quantized_weight"),
        numpy_helper.from_array(bias_scale, "bias_scale"),
        numpy_helper.from_array(bias_zero_point, "bias_zero_point"),
        numpy_helper.from_array(quantized_bias, "quantized_bias"),
    ]

    nodes = [
        helper.make_node(
            "DequantizeLinear",
            ["input", "x_scale", "x_zero_point"],
            ["dequantized_input"],
            name="dequantize_input",
        ),
        helper.make_node(
            "DequantizeLinear",
            ["quantized_weight", "weight_scale", "weight_zero_point"],
            ["dequantized_weight"],
            name="dequantize_weight",
        ),
        helper.make_node(
            "DequantizeLinear",
            ["quantized_bias", "bias_scale", "bias_zero_point"],
            ["dequantized_bias"],
            name="dequantize_bias",
        ),
        helper.make_node(
            "Conv",
            ["dequantized_input", "dequantized_weight", "dequantized_bias"],
            ["conv_output"],
            name="conv",
            pads=[1, 1, 1, 1],
            strides=[1, 1],
        ),
        helper.make_node(
            "QuantizeLinear",
            ["conv_output", "output_scale", "output_zero_point"],
            ["output"],
            name="quantize_output",
        ),
    ]

    graph = helper.make_graph(
        nodes,
        "r004_minimal_qdq_conv",
        [input_info],
        [output_info],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        producer_name="SnapdragonAI-R004",
        producer_version="1",
        opset_imports=[helper.make_opsetid("", 13)],
    )
    model.ir_version = 10
    onnx.checker.check_model(model)
    onnx.save_model(model, path)


def deterministic_input() -> np.ndarray:
    return np.asarray(
        [
            [
                [
                    [108, 113, 118, 123],
                    [128, 133, 138, 143],
                    [148, 144, 140, 136],
                    [132, 128, 124, 120],
                ]
            ]
        ],
        dtype=np.uint8,
    )


def cpu_reference(model_path: Path, test_input: np.ndarray) -> np.ndarray:
    session = ort.InferenceSession(
        str(model_path),
        providers=["CPUExecutionProvider"],
    )
    if session.get_providers() != ["CPUExecutionProvider"]:
        raise ExperimentAbort(f"Unexpected CPU providers: {session.get_providers()}")
    return np.asarray(session.run(["output"], {"input": test_input})[0])


def tensor_signature(value_info: onnx.ValueInfoProto) -> dict[str, Any]:
    tensor_type = value_info.type.tensor_type
    dimensions: list[int | str | None] = []
    for dimension in tensor_type.shape.dim:
        if dimension.HasField("dim_value"):
            dimensions.append(int(dimension.dim_value))
        elif dimension.HasField("dim_param"):
            dimensions.append(dimension.dim_param)
        else:
            dimensions.append(None)
    return {
        "name": value_info.name,
        "element_type": int(tensor_type.elem_type),
        "element_type_name": TensorProto.DataType.Name(tensor_type.elem_type),
        "shape": dimensions,
    }


def attribute_value(attribute: onnx.AttributeProto) -> Any:
    value = helper.get_attribute_value(attribute)
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, tuple):
        return list(value)
    return value


def inspect_wrapper(source_model_path: Path, wrapper_path: Path) -> dict[str, Any]:
    source_model = onnx.load(source_model_path, load_external_data=False)
    wrapper_model = onnx.load(wrapper_path, load_external_data=False)
    onnx.checker.check_model(wrapper_model)

    ep_nodes = [node for node in wrapper_model.graph.node if node.op_type == "EPContext"]
    other_nodes = [
        {"name": node.name, "domain": node.domain, "op_type": node.op_type}
        for node in wrapper_model.graph.node
        if node.op_type != "EPContext"
    ]
    if not ep_nodes:
        raise ExperimentAbort(f"No EPContext node in {wrapper_path}")
    if other_nodes:
        raise ExperimentAbort(f"Unexpected productive ONNX nodes in {wrapper_path}: {other_nodes}")

    node_records = []
    context_paths: list[Path] = []
    for node in ep_nodes:
        attributes = {attr.name: attribute_value(attr) for attr in node.attribute}
        source = str(attributes.get("source", ""))
        embed_mode = int(attributes.get("embed_mode", -1))
        cache_reference = str(attributes.get("ep_cache_context", ""))
        if source != ort_qnn.EP_NAME:
            raise ExperimentAbort(
                f"Expected EPContext source {ort_qnn.EP_NAME!r}, got {source!r}"
            )
        if embed_mode != 0:
            raise ExperimentAbort(f"Expected external context embed_mode=0, got {embed_mode}")
        if not cache_reference:
            raise ExperimentAbort("Missing ep_cache_context")

        relative_context = Path(cache_reference.replace("\\", "/"))
        if relative_context.is_absolute() or ".." in relative_context.parts:
            raise ExperimentAbort(f"Unsafe/non-relative ep_cache_context: {cache_reference}")
        context_path = (wrapper_path.parent / relative_context).resolve()
        if not context_path.is_file() or context_path.stat().st_size == 0:
            raise ExperimentAbort(f"Missing or empty context: {context_path}")
        context_paths.append(context_path)
        node_records.append(
            {
                "name": node.name,
                "domain": node.domain,
                "inputs": list(node.input),
                "outputs": list(node.output),
                "attributes": attributes,
            }
        )

    if len(context_paths) != 1:
        raise ExperimentAbort(f"Expected one external context, got {len(context_paths)}")

    source_inputs = [tensor_signature(item) for item in source_model.graph.input]
    source_outputs = [tensor_signature(item) for item in source_model.graph.output]
    wrapper_inputs = [tensor_signature(item) for item in wrapper_model.graph.input]
    wrapper_outputs = [tensor_signature(item) for item in wrapper_model.graph.output]
    if wrapper_inputs != source_inputs or wrapper_outputs != source_outputs:
        raise ExperimentAbort(
            "Wrapper I/O signature differs from source: "
            f"source={source_inputs, source_outputs}, wrapper={wrapper_inputs, wrapper_outputs}"
        )

    return {
        "epcontext_node_count": len(ep_nodes),
        "epcontext_nodes": node_records,
        "unexpected_nodes": other_nodes,
        "inputs": wrapper_inputs,
        "outputs": wrapper_outputs,
        "context_path": str(context_paths[0]),
        "context_relative_path": os.path.relpath(context_paths[0], wrapper_path.parent),
    }


def compile_build(build_dir: Path, selected_devices: list[Any]) -> Path:
    build_dir.mkdir(parents=False, exist_ok=False)
    wrapper_path = build_dir / WRAPPER_NAME
    provider_options = {"backend_path": str(QNN_BACKEND_PATH)}
    session_options = ort.SessionOptions()
    session_options.add_provider_for_devices(selected_devices, provider_options)

    flags = (
        ort.OrtCompileApiFlags.ERROR_IF_NO_NODES_COMPILED.value
        | ort.OrtCompileApiFlags.ERROR_IF_OUTPUT_FILE_EXISTS.value
    )
    compiler = ort.ModelCompiler(
        session_options,
        str(MODEL_PATH),
        embed_compiled_data_into_model=False,
        flags=flags,
        graph_optimization_level=ort.GraphOptimizationLevel.ORT_DISABLE_ALL,
    )
    compiler.compile_to_file(str(wrapper_path))
    if not wrapper_path.is_file() or wrapper_path.stat().st_size == 0:
        raise ExperimentAbort(f"ModelCompiler did not create {wrapper_path}")
    return wrapper_path


def strict_qnn_run(
    wrapper_path: Path,
    test_input: np.ndarray,
    selected_devices: list[Any],
) -> tuple[np.ndarray, list[str]]:
    session_options = ort.SessionOptions()
    session_options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
    provider_options = {"backend_path": str(QNN_BACKEND_PATH)}
    session_options.add_provider_for_devices(selected_devices, provider_options)
    session = ort.InferenceSession(
        str(wrapper_path),
        sess_options=session_options,
    )
    providers = session.get_providers()
    if ort_qnn.EP_NAME not in providers:
        raise ExperimentAbort(f"Strict session did not expose QNN provider: {providers}")
    output = np.asarray(session.run(["output"], {"input": test_input})[0])
    return output, providers


def error_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, Any]:
    if reference.shape != candidate.shape:
        raise ExperimentAbort(f"Output shape mismatch: {reference.shape} != {candidate.shape}")
    absolute = np.abs(reference.astype(np.float64) - candidate.astype(np.float64))
    denominator = np.maximum(np.abs(reference.astype(np.float64)), 1.0e-12)
    relative = absolute / denominator
    return {
        "array_equal": bool(np.array_equal(reference, candidate)),
        "max_absolute_error": float(np.max(absolute)),
        "max_relative_error": float(np.max(relative)),
        "mean_absolute_error": float(np.mean(absolute)),
    }


def normalized_wrapper_structure(inspection: dict[str, Any]) -> dict[str, Any]:
    normalized_nodes = []
    for node in inspection["epcontext_nodes"]:
        attributes = dict(node["attributes"])
        attributes["ep_cache_context"] = "<external-context>"
        normalized_nodes.append(
            {
                "domain": node["domain"],
                "inputs": node["inputs"],
                "outputs": node["outputs"],
                "attributes": attributes,
            }
        )
    return {
        "nodes": normalized_nodes,
        "inputs": inspection["inputs"],
        "outputs": inspection["outputs"],
        "unexpected_nodes": inspection["unexpected_nodes"],
    }


def manifest_for_build(
    label: str,
    wrapper_path: Path,
    inspection: dict[str, Any],
    providers: list[str],
    output_path: Path,
) -> dict[str, Any]:
    context_path = Path(inspection["context_path"])
    return {
        "experiment": "R-004 Reproducible EPContext Build",
        "build": label,
        "input_model": {
            "path": str(MODEL_PATH),
            "size": MODEL_PATH.stat().st_size,
            "sha256": sha256(MODEL_PATH),
        },
        "wrapper": {
            "path": str(wrapper_path),
            "size": wrapper_path.stat().st_size,
            "sha256": sha256(wrapper_path),
        },
        "context": {
            "path": str(context_path),
            "relative_reference": inspection["context_relative_path"],
            "size": context_path.stat().st_size,
            "sha256": sha256(context_path),
        },
        "qnn_output": {
            "path": str(output_path),
            "size": output_path.stat().st_size,
            "sha256": sha256(output_path),
        },
        "wrapper_validation": inspection,
        "strict_qnn": {
            "cpu_fallback_disabled": True,
            "requested_providers": [ort_qnn.EP_NAME],
            "session_providers": providers,
        },
        "toolchain": {
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
            "onnxruntime_qnn": importlib.metadata.version("onnxruntime-qnn"),
            "qnn_backend_path": str(QNN_BACKEND_PATH),
            "qnn_backend_size": QNN_BACKEND_PATH.stat().st_size,
            "qnn_backend_sha256": sha256(QNN_BACKEND_PATH),
            "available_providers": ort.get_available_providers(),
            "qnn_provider_library_path": str(QNN_PROVIDER_LIBRARY_PATH),
            "qnn_provider_library_size": QNN_PROVIDER_LIBRARY_PATH.stat().st_size,
            "qnn_provider_library_sha256": sha256(QNN_PROVIDER_LIBRARY_PATH),
        },
        "compile_options": {
            "provider": ort_qnn.EP_NAME,
            "provider_options": {"backend_path": str(QNN_BACKEND_PATH)},
            "embed_compiled_data_into_model": False,
            "graph_optimization_level": "ORT_DISABLE_ALL",
            "flags": ["ERROR_IF_NO_NODES_COMPILED", "ERROR_IF_OUTPUT_FILE_EXISTS"],
        },
    }


def write_markdown_report(report: dict[str, Any]) -> None:
    path = EXPERIMENT_DIR / "R004_REPORT.md"
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}")
    a = report["build_a"]
    b = report["build_b"]
    accuracy_a = report["accuracy"]["cpu_vs_build_a"]
    accuracy_b = report["accuracy"]["cpu_vs_build_b"]
    text = f"""# R-004 – Reproducible EPContext Build

## Ergebnis

**{report['recommendation']['decision']}** für einen SDXL-VAE-Piloten: {report['recommendation']['reason']}

## Testmodell

Statischer Q/DQ-Conv-Graph, Opset 13, UINT8-I/O `[1, 1, 4, 4]`, deterministische INT8-Gewichte und INT32-Bias. CPU-Referenz und QNN-Ausgaben verwenden denselben gespeicherten Testinput.

## Toolchain und Optionen

- ONNX Runtime: `{report['toolchain']['onnxruntime']}`
- onnxruntime-qnn: `{report['toolchain']['onnxruntime_qnn']}`
- QnnHtp.dll: `{report['toolchain']['qnn_backend_path']}`
- Provider: ausschließlich `QNNExecutionProvider`
- Externer Context: `embed_compiled_data_into_model=False`
- Graphoptimierung: `ORT_DISABLE_ALL`
- Flags: `ERROR_IF_NO_NODES_COMPILED`, `ERROR_IF_OUTPUT_FILE_EXISTS`
- Strict Load: `session.disable_cpu_ep_fallback=1`

## Reproduzierbarkeit

| Artefakt | Build A | Build B | Gleich |
|---|---:|---:|:---:|
| Wrappergröße | {a['wrapper']['size']} | {b['wrapper']['size']} | {report['reproducibility']['wrapper_sizes_equal']} |
| Wrapper SHA-256 | `{a['wrapper']['sha256']}` | `{b['wrapper']['sha256']}` | {report['reproducibility']['wrapper_hashes_equal']} |
| Contextgröße | {a['context']['size']} | {b['context']['size']} | {report['reproducibility']['context_sizes_equal']} |
| Context SHA-256 | `{a['context']['sha256']}` | `{b['context']['sha256']}` | {report['reproducibility']['context_hashes_equal']} |

Bitgleiche Gesamtartefakte: **{report['reproducibility']['bitwise_reproducible']}**  
Wrapperstruktur identisch: **{report['reproducibility']['wrapper_structure_identical']}**  
QNN-Ausgaben A/B identisch: **{report['accuracy']['build_a_vs_build_b']['array_equal']}**

## Genauigkeit

| Vergleich | Max. absolut | Max. relativ | Mittel absolut |
|---|---:|---:|---:|
| CPU vs Build A | {accuracy_a['max_absolute_error']:.12g} | {accuracy_a['max_relative_error']:.12g} | {accuracy_a['mean_absolute_error']:.12g} |
| CPU vs Build B | {accuracy_b['max_absolute_error']:.12g} | {accuracy_b['max_relative_error']:.12g} | {accuracy_b['mean_absolute_error']:.12g} |
| Build A vs Build B | {report['accuracy']['build_a_vs_build_b']['max_absolute_error']:.12g} | {report['accuracy']['build_a_vs_build_b']['max_relative_error']:.12g} | {report['accuracy']['build_a_vs_build_b']['mean_absolute_error']:.12g} |

Die relative Maximalabweichung ist definiert als `abs(reference-candidate) / max(abs(reference), 1e-12)`.

## Strict-QNN-Nachweis

Beide Wrapper wurden mit ausschließlich `QNNExecutionProvider` geladen. CPU-Fallback war über `session.disable_cpu_ep_fallback=1` deaktiviert. Beide Sessions führten den deterministischen Testinput ohne Fallback aus.
"""
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def main() -> None:
    qnn_package_version = importlib.metadata.version("onnxruntime-qnn")
    if ort.__version__ != EXPECTED_ORT_VERSION:
        raise ExperimentAbort(f"Expected ORT {EXPECTED_ORT_VERSION}, got {ort.__version__}")
    if qnn_package_version != EXPECTED_QNN_PACKAGE_VERSION:
        raise ExperimentAbort(
            f"Expected onnxruntime-qnn {EXPECTED_QNN_PACKAGE_VERSION}, got {qnn_package_version}"
        )
    if not QNN_BACKEND_PATH.is_file():
        raise ExperimentAbort(f"QNN backend does not exist: {QNN_BACKEND_PATH}")
    if not QNN_PROVIDER_LIBRARY_PATH.is_file():
        raise ExperimentAbort(f"QNN provider library does not exist: {QNN_PROVIDER_LIBRARY_PATH}")

    ort.register_execution_provider_library(
        ort_qnn.get_ep_name(),
        str(QNN_PROVIDER_LIBRARY_PATH),
    )
    if not hasattr(ort, "get_ep_devices") or not hasattr(
        ort.SessionOptions, "add_provider_for_devices"
    ):
        raise ExperimentAbort("ORT lacks the required explicit EP-device APIs")
    selected_devices = [
        device for device in ort.get_ep_devices() if device.ep_name == ort_qnn.EP_NAME
    ]
    if not selected_devices:
        raise ExperimentAbort("No explicit QNNExecutionProvider device is available")

    reserved_paths = [
        MODEL_PATH,
        INPUT_PATH,
        CPU_OUTPUT_PATH,
        EXPERIMENT_DIR / "build_manifest_a.json",
        EXPERIMENT_DIR / "build_manifest_b.json",
        EXPERIMENT_DIR / "comparison_report.json",
        EXPERIMENT_DIR / "R004_REPORT.md",
        *(EXPERIMENT_DIR / name for name in BUILD_NAMES),
    ]
    existing = [str(path) for path in reserved_paths if path.exists()]
    if existing:
        raise ExperimentAbort(f"Refusing to overwrite existing experiment artifacts: {existing}")

    make_test_model(MODEL_PATH)
    test_input = deterministic_input()
    save_npy_exclusive(INPUT_PATH, test_input)
    reference_output = cpu_reference(MODEL_PATH, test_input)
    save_npy_exclusive(CPU_OUTPUT_PATH, reference_output)

    builds: dict[str, dict[str, Any]] = {}
    outputs: dict[str, np.ndarray] = {}
    for label, directory_name in zip(("a", "b"), BUILD_NAMES, strict=True):
        build_dir = EXPERIMENT_DIR / directory_name
        wrapper_path = compile_build(build_dir, selected_devices)
        inspection = inspect_wrapper(MODEL_PATH, wrapper_path)
        qnn_output, providers = strict_qnn_run(wrapper_path, test_input, selected_devices)
        output_path = build_dir / "qnn_output.npy"
        save_npy_exclusive(output_path, qnn_output)
        builds[label] = manifest_for_build(
            label.upper(), wrapper_path, inspection, providers, output_path
        )
        outputs[label] = qnn_output

    manifest_a_path = EXPERIMENT_DIR / "build_manifest_a.json"
    manifest_b_path = EXPERIMENT_DIR / "build_manifest_b.json"
    write_json_exclusive(manifest_a_path, builds["a"])
    write_json_exclusive(manifest_b_path, builds["b"])

    wrapper_structure_identical = normalized_wrapper_structure(
        builds["a"]["wrapper_validation"]
    ) == normalized_wrapper_structure(builds["b"]["wrapper_validation"])
    wrapper_hashes_equal = builds["a"]["wrapper"]["sha256"] == builds["b"]["wrapper"]["sha256"]
    context_hashes_equal = builds["a"]["context"]["sha256"] == builds["b"]["context"]["sha256"]
    wrapper_sizes_equal = builds["a"]["wrapper"]["size"] == builds["b"]["wrapper"]["size"]
    context_sizes_equal = builds["a"]["context"]["size"] == builds["b"]["context"]["size"]
    accuracy_a = error_metrics(reference_output, outputs["a"])
    accuracy_b = error_metrics(reference_output, outputs["b"])
    accuracy_ab = error_metrics(outputs["a"], outputs["b"])
    bitwise_reproducible = wrapper_hashes_equal and context_hashes_equal
    accuracy_within_one_output_lsb = (
        accuracy_a["max_absolute_error"] <= OUTPUT_QUANTIZATION_SCALE + 1.0e-7
        and accuracy_b["max_absolute_error"] <= OUTPUT_QUANTIZATION_SCALE + 1.0e-7
    )
    functional_reproducibility = accuracy_ab["array_equal"] and wrapper_structure_identical
    go = bitwise_reproducible and functional_reproducibility and accuracy_within_one_output_lsb
    reason = (
        "bitgleiche Wrapper/Contexts, identische QNN-Ausgaben und CPU-Abweichung innerhalb eines "
        "Output-Quantisierungsschritts"
        if go
        else "mindestens ein Reproduzierbarkeits-, Struktur- oder Genauigkeitskriterium ist nicht erfüllt"
    )

    report = {
        "experiment": "R-004 Reproducible EPContext Build",
        "status": "PASS",
        "test_model": {
            "path": str(MODEL_PATH),
            "sha256": sha256(MODEL_PATH),
            "graph": "Q/DQ Conv",
            "opset": 13,
            "input_shape": [1, 1, 4, 4],
            "output_shape": [1, 1, 4, 4],
            "input_type": "UINT8",
            "output_type": "UINT8",
            "deterministic_quantized_weights": True,
        },
        "toolchain": builds["a"]["toolchain"],
        "build_a": builds["a"],
        "build_b": builds["b"],
        "reproducibility": {
            "input_model_hashes_equal": builds["a"]["input_model"]["sha256"]
            == builds["b"]["input_model"]["sha256"],
            "wrapper_hashes_equal": wrapper_hashes_equal,
            "wrapper_sizes_equal": wrapper_sizes_equal,
            "context_hashes_equal": context_hashes_equal,
            "context_sizes_equal": context_sizes_equal,
            "wrapper_structure_identical": wrapper_structure_identical,
            "bitwise_reproducible": bitwise_reproducible,
            "functionally_reproducible": functional_reproducibility,
        },
        "accuracy": {
            "relative_error_definition": "abs(reference-candidate) / max(abs(reference), 1e-12)",
            "cpu_vs_build_a": accuracy_a,
            "cpu_vs_build_b": accuracy_b,
            "build_a_vs_build_b": accuracy_ab,
            "cpu_tolerance": {
                "criterion": "max absolute error <= one output quantization scale",
                "output_quantization_scale": OUTPUT_QUANTIZATION_SCALE,
                "passed": accuracy_within_one_output_lsb,
            },
        },
        "strict_qnn": {
            "build_a": builds["a"]["strict_qnn"],
            "build_b": builds["b"]["strict_qnn"],
            "passed": True,
        },
        "recommendation": {
            "decision": "GO" if go else "NO-GO",
            "target": "SDXL VAE pilot",
            "reason": reason,
        },
    }
    write_json_exclusive(EXPERIMENT_DIR / "comparison_report.json", report)
    write_markdown_report(report)
    print(json.dumps({"status": "PASS", "decision": report["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
