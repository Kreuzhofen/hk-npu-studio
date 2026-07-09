from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("OnnxComponentInspector")


class OnnxComponentInspector:
    """Reads ONNX Runtime component metadata without owning inference logic."""

    @staticmethod
    def inspect(component_name: str, component_path: str | None) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "component": component_name,
            "path": component_path or "",
            "exists": False,
            "loadable": False,
            "inputs": [],
            "outputs": [],
            "error": "",
        }
        if not component_path:
            metadata["error"] = "Component path is empty."
            return metadata

        path = Path(component_path)
        metadata["exists"] = path.exists()
        if not path.exists() or not path.is_file():
            metadata["error"] = "Component file does not exist."
            return metadata

        try:
            import onnxruntime as ort
            session = ort.InferenceSession(str(path))
            metadata["inputs"] = [
                {
                    "name": item.name,
                    "shape": [str(value) for value in item.shape],
                    "type": item.type,
                }
                for item in session.get_inputs()
            ]
            metadata["outputs"] = [
                {
                    "name": item.name,
                    "shape": [str(value) for value in item.shape],
                    "type": item.type,
                }
                for item in session.get_outputs()
            ]
            metadata["loadable"] = True
            del session
        except Exception as exc:
            metadata["error"] = str(exc)
        return metadata

    @staticmethod
    def inspect_package(package: Any, component_names: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        return {
            name: OnnxComponentInspector.inspect(name, package.get_component_path(name))
            for name in component_names
        }

    @staticmethod
    def log_metadata(metadata: dict[str, dict[str, Any]]) -> None:
        for name, info in metadata.items():
            logger.info("[ONNX Metadata] %s loadable=%s path=%s", name, info.get("loadable"), info.get("path"))
            print(f"[ONNX Metadata] {name}: loadable={info.get('loadable')} path={info.get('path')}")
            if info.get("inputs"):
                print(f"  inputs : {info.get('inputs')}")
            if info.get("outputs"):
                print(f"  outputs: {info.get('outputs')}")
            if info.get("error"):
                print(f"  error  : {info.get('error')}")
