from __future__ import annotations

import logging
from engine.logging_config import get_logger
from pathlib import Path
from typing import Any

logger = get_logger("OnnxComponentInspector")


_TENSOR_DTYPES = {
    0: "UNDEFINED", 1: "FLOAT", 2: "UINT8", 3: "INT8", 4: "UINT16", 5: "INT16",
    6: "INT32", 7: "INT64", 8: "STRING", 9: "BOOL", 10: "FLOAT16", 11: "DOUBLE",
    12: "UINT32", 13: "UINT64", 14: "COMPLEX64", 15: "COMPLEX128", 16: "BFLOAT16",
}


def _varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data) and shift < 70:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    raise ValueError("Invalid protobuf varint")


def _fields(data: bytes) -> list[tuple[int, int, int | bytes]]:
    result: list[tuple[int, int, int | bytes]] = []
    offset = 0
    while offset < len(data):
        tag, offset = _varint(data, offset)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, offset = _varint(data, offset)
        elif wire == 1:
            value, offset = data[offset:offset + 8], offset + 8
        elif wire == 2:
            length, offset = _varint(data, offset)
            value, offset = data[offset:offset + length], offset + length
        elif wire == 5:
            value, offset = data[offset:offset + 4], offset + 4
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire}")
        if offset > len(data):
            raise ValueError("Truncated protobuf field")
        result.append((number, wire, value))
    return result


def _text(value: int | bytes) -> str:
    return bytes(value).decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)


def _first(fields: list[tuple[int, int, int | bytes]], number: int, default: Any = None) -> Any:
    return next((value for field, _wire, value in fields if field == number), default)


class OnnxComponentInspector:
    """Inspect ONNX contracts without loading external tensor data."""

    DEFAULT_PARSE_LIMIT_BYTES = 64 * 1024 * 1024

    @staticmethod
    def _dimension(dimension: bytes) -> int | str | None:
        fields = _fields(dimension)
        value = _first(fields, 1)
        if isinstance(value, int):
            return value
        parameter = _first(fields, 2)
        if isinstance(parameter, bytes):
            return _text(parameter)
        return None

    @classmethod
    def _value_info(cls, value: bytes) -> dict[str, Any]:
        value_fields = _fields(value)
        type_message = _first(value_fields, 2, b"")
        tensor_message = _first(_fields(type_message), 1, b"") if isinstance(type_message, bytes) else b""
        tensor_fields = _fields(tensor_message)
        elem_type = int(_first(tensor_fields, 1, 0))
        shape_message = _first(tensor_fields, 2, b"")
        dimensions = [item for field, wire, item in _fields(shape_message) if field == 1 and wire == 2] if isinstance(shape_message, bytes) else []
        shape = [cls._dimension(bytes(item)) for item in dimensions]
        return {
            "name": _text(_first(value_fields, 1, b"")),
            "shape": shape,
            "dynamic_dimensions": [index for index, item in enumerate(shape) if not isinstance(item, int) or item <= 0],
            "dtype": _TENSOR_DTYPES.get(elem_type, f"UNKNOWN_{elem_type}"),
        }

    @staticmethod
    def _attribute(attribute: bytes) -> tuple[str, Any]:
        fields = _fields(attribute)
        name = _text(_first(fields, 1, b""))
        if (value := _first(fields, 4)) is not None:
            return name, _text(value)
        if (value := _first(fields, 3)) is not None:
            return name, int(value)
        return name, None

    @classmethod
    def inspect_static(
        cls,
        component_name: str,
        component_path: str | Path | None,
        *,
        parse_limit_bytes: int | None = None,
    ) -> dict[str, Any]:
        limit = parse_limit_bytes if parse_limit_bytes is not None else cls.DEFAULT_PARSE_LIMIT_BYTES
        result: dict[str, Any] = {
            "component": component_name,
            "path": str(component_path or ""),
            "exists": False,
            "readable": False,
            "size_bytes": 0,
            "parsed": False,
            "parse_skipped_reason": "",
            "ir_version": None,
            "opsets": [],
            "inputs": [],
            "outputs": [],
            "node_count": None,
            "operator_types": [],
            "initializer_dtypes": [],
            "external_data": [],
            "epcontext_nodes": [],
            "non_epcontext_nodes": [],
            "error": "",
        }
        if not component_path:
            result["error"] = "Component path is empty."
            return result
        path = Path(component_path)
        result["exists"] = path.is_file()
        if not result["exists"]:
            result["error"] = "Component file does not exist."
            return result
        try:
            result["size_bytes"] = path.stat().st_size
            with path.open("rb") as stream:
                stream.read(1)
            result["readable"] = True
        except OSError as exc:
            result["error"] = str(exc)
            return result
        if path.suffix.lower() != ".onnx":
            result["parse_skipped_reason"] = "not_onnx"
            return result
        if result["size_bytes"] > limit:
            result["parse_skipped_reason"] = "onnx_file_exceeds_safe_parse_limit"
            return result
        try:
            model_data = path.read_bytes()
            model_fields = _fields(model_data)
            graph_data = _first(model_fields, 7, b"")
            if not isinstance(graph_data, bytes):
                raise ValueError("ONNX graph field is missing")
            graph_fields = _fields(graph_data)
            result["parsed"] = True
            result["ir_version"] = int(_first(model_fields, 1, 0))
            opsets = []
            for field, wire, value in model_fields:
                if field == 8 and wire == 2:
                    entries = _fields(bytes(value))
                    opsets.append({"domain": _text(_first(entries, 1, b"")) or "ai.onnx", "version": int(_first(entries, 2, 0))})
            result["opsets"] = sorted(opsets, key=lambda item: item["domain"])
            result["inputs"] = [cls._value_info(bytes(value)) for field, wire, value in graph_fields if field == 11 and wire == 2]
            result["outputs"] = [cls._value_info(bytes(value)) for field, wire, value in graph_fields if field == 12 and wire == 2]
            nodes = [bytes(value) for field, wire, value in graph_fields if field == 1 and wire == 2]
            result["node_count"] = len(nodes)
            node_records: list[tuple[list[tuple[int, int, int | bytes]], str]] = []
            for node in nodes:
                fields = _fields(node)
                node_records.append((fields, _text(_first(fields, 4, b""))))
            result["operator_types"] = sorted({op for _fields_value, op in node_records})
            result["non_epcontext_nodes"] = [op for _fields_value, op in node_records if op != "EPContext"]
            initializers = [bytes(value) for field, wire, value in graph_fields if field == 5 and wire == 2]
            for initializer in initializers:
                init_fields = _fields(initializer)
                dtype = _TENSOR_DTYPES.get(int(_first(init_fields, 2, 0)), f"UNKNOWN_{_first(init_fields, 2, 0)}")
                if dtype not in result["initializer_dtypes"]:
                    result["initializer_dtypes"].append(dtype)
                external_entries = [bytes(value) for field, wire, value in init_fields if field == 13 and wire == 2]
                if int(_first(init_fields, 14, 0)) == 1 or external_entries:
                    entries = {}
                    for external in external_entries:
                        entry_fields = _fields(external)
                        entries[_text(_first(entry_fields, 1, b""))] = _text(_first(entry_fields, 2, b""))
                    result["external_data"].append({
                        "tensor": _text(_first(init_fields, 8, b"")),
                        "location": entries.get("location", ""),
                        "offset": int(entries.get("offset", "0") or 0),
                        "length": int(entries.get("length", "0") or 0),
                    })
            result["initializer_dtypes"].sort()
            for node_fields, op_type in node_records:
                if op_type == "EPContext":
                    attrs = dict(cls._attribute(bytes(value)) for field, wire, value in node_fields if field == 5 and wire == 2)
                    result["epcontext_nodes"].append({
                        "name": _text(_first(node_fields, 3, b"")),
                        "domain": _text(_first(node_fields, 7, b"")),
                        "attributes": attrs,
                    })
            del model_data
        except Exception as exc:
            result["error"] = str(exc)
        return result

    @classmethod
    def inspect(cls, component_name: str, component_path: str | None) -> dict[str, Any]:
        """Backward-compatible metadata view; static and free of runtime sessions."""
        metadata = cls.inspect_static(component_name, component_path)
        metadata["loadable"] = metadata["parsed"]
        metadata["inputs"] = [
            {"name": item["name"], "shape": item["shape"], "type": item["dtype"]}
            for item in metadata["inputs"]
        ]
        metadata["outputs"] = [
            {"name": item["name"], "shape": item["shape"], "type": item["dtype"]}
            for item in metadata["outputs"]
        ]
        return metadata

    @staticmethod
    def inspect_package(package: Any, component_names: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        return {name: OnnxComponentInspector.inspect(name, package.get_component_path(name)) for name in component_names}

    @staticmethod
    def log_metadata(metadata: dict[str, dict[str, Any]]) -> None:
        for name, info in metadata.items():
            logger.info("[ONNX Metadata] %s loadable=%s path=%s", name, info.get("loadable"), info.get("path"))
