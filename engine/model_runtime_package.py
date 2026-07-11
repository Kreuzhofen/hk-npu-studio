from __future__ import annotations
import json
from typing import Any
from pathlib import Path
from controllers.model_repository import ModelCapabilities

class ModelRuntimePackage:
    """
    Model-independent runtime container that represents a packaged set of model components,
    their resolved filesystem paths, execution runtimes (ONNX / QNN), and capabilities.
    Designed to prepare and validate components needed for stable diffusion generation.
    """
    def __init__(
        self,
        model_id: str,
        base_path: str | Path,
        capabilities: ModelCapabilities,
        component_paths: dict[str, str] | None = None,
        component_runtimes: dict[str, str] | None = None,
        package_version: str = "1.0.0",
        author: str = "",
        display_name: str = ""
    ) -> None:
        self.model_id = model_id
        self.base_path = Path(base_path)
        self.capabilities = capabilities
        self.package_version = package_version
        self.author = author
        self.display_name = display_name
        
        # Paths for supported components: tokenizer, optional tokenizer_2, text_encoder, text_encoder_2, unet, vae_decoder, scheduler, optional qnn_dlc
        self.component_paths = component_paths or {}
        # Runtime types for each component (e.g. "ONNX", "QNN", "CPU", etc.)
        self.component_runtimes = component_runtimes or {}
        
    def get_component_path(self, component_name: str) -> str | None:
        """
        Get the resolved filesystem path for a specific component.
        """
        return self.component_paths.get(component_name)
        
    def get_component_runtime(self, component_name: str) -> str | None:
        """
        Get the execution runtime for a specific component.
        """
        return self.component_runtimes.get(component_name)
        
    def is_valid_package(self) -> bool:
        """
        Validates that all declared required paths exist on disk.
        tokenizer_2 is optional for SDXL packages and may fall back to tokenizer.
        """
        for name, path_str in self.component_paths.items():
            if name in ["tokenizer_2", "text_encoder_2", "qnn_dlc"]:
                continue
            if path_str:
                p = Path(path_str)
                if not p.exists():
                    return False
        return True
        
    def verify_components(self) -> dict[str, str]:
        """
        Verify status of each expected component in the package.
        tokenizer_2, text_encoder_2 and qnn_dlc are optional depending on the package declaration and capabilities.
        """
        statuses = {}
        if self.capabilities.qnn_dlc_runtime and not self.capabilities.onnx_runtime:
            expected_components = ["qnn_dlc"]
            optional_components: list[str] = []
        else:
            expected_components = ["tokenizer", "text_encoder", "unet", "vae_decoder", "scheduler"]
            optional_components = ["tokenizer_2", "qnn_dlc", "text_encoder_2"]

            # If text_encoder_2 is declared, expect it to be present
            if self.component_paths.get("text_encoder_2"):
                expected_components.append("text_encoder_2")
                optional_components.remove("text_encoder_2")

        for name in expected_components:
            path_str = self.component_paths.get(name)
            if not path_str:
                statuses[name] = "MISSING"
                continue

            p = Path(path_str)
            if not p.exists():
                statuses[name] = "MISSING"
                continue

            statuses[name] = self._component_status(name, p)

        for name in optional_components:
            path_str = self.component_paths.get(name)
            if not path_str:
                statuses[name] = "FALLBACK"
                continue

            p = Path(path_str)
            if not p.exists():
                statuses[name] = "FALLBACK"
                continue

            statuses[name] = self._component_status(name, p, fallback_on_invalid=True)

        return statuses

    def _component_status(self, name: str, path: Path, fallback_on_invalid: bool = False) -> str:
        if name == "qnn_dlc":
            if path.is_file() and path.suffix.lower() == ".dlc" and path.stat().st_size > 0:
                return "READY"
            return "FOUND" if fallback_on_invalid and path.exists() else "INVALID"

        if name in ["tokenizer", "tokenizer_2", "scheduler"]:
            if not path.is_dir():
                return "INVALID"
            try:
                return "READY" if len(list(path.iterdir())) > 0 else "FOUND"
            except Exception:
                return "INVALID"

        if path.is_file():
            # Support QNN precompiled wrappers (ONNX files pointing to QNN context binaries)
            # which can be extremely small (<= 1024 bytes).
            if path.suffix.lower() == ".onnx":
                parent_dir = path.parent
                stem = path.stem
                candidates = (
                    parent_dir / f"{name}_qairt_context.bin",
                    parent_dir / f"{stem}_qairt_context.bin",
                    parent_dir / f"{stem}.bin",
                )
                cb = next((candidate for candidate in candidates if candidate.exists()), None)
                if cb is not None:
                    if cb.stat().st_size > 0:
                        return "READY"
                    else:
                        return "INVALID"
            return "FOUND" if path.stat().st_size <= 1024 else "READY"
        return "INVALID"

    def validation_detail(self) -> dict[str, str]:
        """Return a stable product-facing package validation code and path."""
        if not (self.base_path / "package.json").is_file():
            return {"code": "INCOMPLETE", "message": "Package manifest missing", "path": str(self.base_path / "package.json")}
        if not (self.base_path / "metadata.json").is_file():
            return {"code": "INCOMPLETE", "message": "Model metadata missing", "path": str(self.base_path / "metadata.json")}
        statuses = self.verify_components()
        labels = {"tokenizer": "MISSING TOKENIZER", "scheduler": "MISSING SCHEDULER"}
        for name in ("tokenizer", "scheduler"):
            if statuses.get(name) != "READY":
                return {"code": labels[name], "message": labels[name].title(), "path": str(self.component_paths.get(name, ""))}
        for name in ("text_encoder", "unet", "vae_decoder"):
            path = Path(self.component_paths.get(name, ""))
            if not path.is_file():
                return {"code": "MISSING WRAPPER", "message": "ONNX wrapper missing", "path": str(path)}
            if self._component_status(name, path) != "READY":
                return {"code": "MISSING CONTEXT", "message": "Required QNN context binary not found", "path": str(self._expected_context_path(name, path))}
        return {"code": "READY", "message": "Package ready", "path": str(self.base_path)}

    def _expected_context_path(self, component_name: str, wrapper_path: Path) -> Path:
        """Resolve the package's declared or conventional external QNN context path."""
        metadata_path = self.base_path / "metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            metadata = {}

        model_files = metadata.get("model_files", {})
        stem_context = wrapper_path.with_suffix(".bin")
        if isinstance(model_files, dict) and stem_context.name in model_files:
            return stem_context
        return wrapper_path.parent / f"{component_name}_qairt_context.bin"

    def is_fully_ready(self) -> bool:
        """
        Checks if all required components are in the READY status.
        """
        statuses = self.verify_components()
        optional = {"tokenizer_2"}
        if not self.capabilities.qnn_dlc_runtime:
            optional.add("qnn_dlc")
        if not self.component_paths.get("text_encoder_2"):
            optional.add("text_encoder_2")

        required = {name: status for name, status in statuses.items() if name not in optional}
        return all(status == "READY" for status in required.values())

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize metadata for debugging/logging.
        """
        return {
            "model_id": self.model_id,
            "base_path": str(self.base_path.as_posix()),
            "capabilities": self.capabilities.to_dict(),
            "component_paths": self.component_paths,
            "component_runtimes": self.component_runtimes,
            "package_version": self.package_version,
            "author": self.author,
            "display_name": self.display_name,
            "verification_status": self.verify_components(),
            "is_fully_ready": self.is_fully_ready()
        }







