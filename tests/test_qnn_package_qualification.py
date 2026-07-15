from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from engine.qnn_package_qualification import QnnPackageQualifier, deterministic_json


class _StrictSession:
    def get_providers(self) -> list[str]:
        return ["QNNExecutionProvider"]


def _varint(value: int) -> bytes:
    output = bytearray()
    while value > 0x7F:
        output.append((value & 0x7F) | 0x80)
        value >>= 7
    output.append(value)
    return bytes(output)


def _v(number: int, value: int) -> bytes:
    return _varint(number << 3) + _varint(value)


def _b(number: int, value: bytes | str) -> bytes:
    payload = value.encode() if isinstance(value, str) else value
    return _varint((number << 3) | 2) + _varint(len(payload)) + payload


def _value_info(name: str, dynamic: bool) -> bytes:
    dimension = _b(2, "batch") if dynamic else _v(1, 1)
    dimension_2 = _v(1, 4)
    shape = _b(1, dimension) + _b(1, dimension_2)
    tensor_type = _v(1, 4) + _b(2, shape)
    return _b(1, name) + _b(2, _b(1, tensor_type))


def _attribute(name: str, value: str | int) -> bytes:
    payload = _b(1, name) + _v(20, 3 if isinstance(value, str) else 2)
    return payload + (_b(4, value) if isinstance(value, str) else _v(3, value))


def _node(op_type: str, *, name: str = "", attributes: dict[str, str | int] | None = None) -> bytes:
    payload = _b(1, "input") + _b(2, "output") + _b(4, op_type)
    if name:
        payload += _b(3, name)
    if op_type == "EPContext":
        payload += _b(7, "com.microsoft")
    for key, value in (attributes or {}).items():
        payload += _b(5, _attribute(key, value))
    return payload


class QnnPackageQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _wrapper(self, name: str, *, context: bool = True, dynamic: bool = False, cpu_node: bool = False) -> None:
        nodes = [_node("EPContext", name=name, attributes={"source": "Qnn", "embed_mode": 0, "ep_cache_context": f"{name}.bin"})]
        if cpu_node:
            nodes.append(_node("Identity"))
        initializer = _v(1, 1) + _v(2, 1) + _b(8, "unused_fp32")
        graph = b"".join(_b(1, node) for node in nodes) + _b(2, name) + _b(5, initializer) + _b(11, _value_info("input", dynamic)) + _b(12, _value_info("output", dynamic))
        opset = _v(2, 13)
        model = _v(1, 10) + _b(7, graph) + _b(8, opset)
        (self.root / f"{name}.onnx").write_bytes(model)
        if context:
            (self.root / f"{name}.bin").write_bytes(b"qnn-context")

    def _package(self, *, missing_context: str | None = None, dynamic: str | None = None, cpu_node: str | None = None, qnn_runtime: bool = True) -> None:
        for directory in ("tokenizer", "scheduler"):
            (self.root / directory).mkdir()
            (self.root / directory / "config.json").write_text("{}", encoding="utf-8")
        components: dict[str, dict[str, str]] = {
            "tokenizer": {"path": "tokenizer", "runtime": "CPU"},
            "scheduler": {"path": "scheduler", "runtime": "CPU"},
        }
        for name in ("text_encoder", "unet", "vae_decoder"):
            self._wrapper(name, context=name != missing_context, dynamic=name == dynamic, cpu_node=name == cpu_node)
            components[name] = {"path": f"{name}.onnx", "runtime": "QNN"}
        manifest = {"model_id": "fixture", "package_version": "1.0", "capabilities": {"txt2img": True, "qnn_runtime": qnn_runtime}, "components": components}
        (self.root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_missing_component_is_rejected(self) -> None:
        self._package()
        manifest = json.loads((self.root / "package.json").read_text(encoding="utf-8"))
        del manifest["components"]["unet"]
        (self.root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
        report = QnnPackageQualifier().inspect(self.root)
        self.assertEqual("REJECTED", report["qualification_status"])
        self.assertIn("REQUIRED_COMPONENT_MISSING", report["rejection_reasons"])

    def test_dynamic_required_shape_is_rejected(self) -> None:
        self._package(dynamic="unet")
        report = QnnPackageQualifier().inspect(self.root)
        self.assertIn("REQUIRED_STATIC_SHAPE_MISSING", report["rejection_reasons"])

    def test_large_fp32_model_is_rejected(self) -> None:
        self._package()
        report = QnnPackageQualifier(fp32_large_limit_bytes=1).inspect(self.root)
        self.assertIn("UNREALISTIC_FP32_LARGE_MODEL", report["rejection_reasons"])

    def test_qnn_context_present_qualifies_statically(self) -> None:
        self._package()
        report = QnnPackageQualifier().inspect(self.root)
        self.assertEqual("CONDITIONALLY_QUALIFIED", report["qualification_status"])

    def test_qnn_context_missing_is_rejected(self) -> None:
        self._package(missing_context="unet")
        report = QnnPackageQualifier().inspect(self.root)
        self.assertIn("QNN_CONTEXT_MISSING", report["rejection_reasons"])

    def test_manifest_contradiction_is_rejected(self) -> None:
        self._package(qnn_runtime=False)
        report = QnnPackageQualifier().inspect(self.root)
        self.assertFalse(report["evidence"]["static_precheck_passed"])
        self.assertIn("QNN_RUNTIME_NOT_DECLARED", report["warnings"])

    def test_productive_cpu_node_in_wrapper_is_rejected(self) -> None:
        self._package(cpu_node="vae_decoder")
        report = QnnPackageQualifier().inspect(self.root)
        self.assertIn("EPCONTEXT_CPU_NODES_PRESENT", report["rejection_reasons"])

    def test_strict_load_failure_is_rejected(self) -> None:
        self._package()

        def fail(_path: Path, _name: str):
            raise RuntimeError("strict failure")

        report = QnnPackageQualifier(strict_loader=fail).qualify(self.root, strict=True)
        self.assertEqual("REJECTED", report["qualification_status"])
        self.assertIn("STRICT_QNN_LOAD_FAILED", report["rejection_reasons"])

    def test_positive_productive_qnn_package_contract(self) -> None:
        package = Path(__file__).resolve().parents[1] / "models" / "stable_diffusion_v2_1"
        report = QnnPackageQualifier(strict_loader=lambda _path, _name: _StrictSession()).qualify(package, strict=True, timestamp="2026-07-15T00:00:00+00:00")
        self.assertEqual("CONDITIONALLY_QUALIFIED", report["qualification_status"])
        self.assertEqual(3, report["evidence"]["strict_load_passed_components"])
        self.assertTrue(all(item.get("epcontext_nodes") for item in report["components"] if item.get("runtime") == "QNN"))

    def test_deterministic_json_structure(self) -> None:
        self._package()
        qualifier = QnnPackageQualifier()
        first = qualifier.inspect(self.root, timestamp="2026-07-15T00:00:00+00:00")
        second = qualifier.inspect(self.root, timestamp="2026-07-15T00:00:00+00:00")
        first["memory_assessment"] = second["memory_assessment"]
        self.assertEqual(deterministic_json(first), deterministic_json(second))

    def test_compile_not_permitted_above_size_limit(self) -> None:
        self._package()
        (self.root / "optional.bin").write_bytes(b"01234567890")
        manifest = json.loads((self.root / "package.json").read_text(encoding="utf-8"))
        manifest["components"]["optional"] = {"path": "optional.bin", "runtime": "ONNX"}
        (self.root / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
        report = QnnPackageQualifier(build_limit_bytes=10).qualify(self.root, strict=False, allow_build=True)
        self.assertFalse(report["build_assessment"]["permitted"])
        self.assertEqual("component_exceeds_build_size_limit", report["build_assessment"]["reason"])
        self.assertFalse(report["evidence"]["compile_attempted"])


if __name__ == "__main__":
    unittest.main()
