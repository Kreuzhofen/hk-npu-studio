from __future__ import annotations

import os
import logging
from engine.logging_config import get_logger
from pathlib import Path
from typing import Any, TypedDict

from controllers.model_repository import ModelRepository

logger = get_logger("ModelLoaderService")


class ModelLoadPlan(TypedDict):
    model_id: str
    model_path: str
    files: list[str]
    backend: str
    steps: list[str]


class ModelResolveResult:
    """
    Structured outcome returned by resolve_model().
    Provides model metadata, paths, backend information and warning lists.
    """
    def __init__(
        self,
        success: bool,
        model_id: str,
        model_path: str | None = None,
        files: list[str] | None = None,
        backend: str = "Unknown",
        message: str = "",
        warnings: list[str] | None = None
    ) -> None:
        self.success = success
        self.model_id = model_id
        self.model_path = model_path
        self.files = files or []
        self.backend = backend
        self.message = message
        self.warnings = warnings or []


class ModelLoaderService:
    """
    Foundation service for resolving and loading installed model metadata.
    Uses ModelRepository as the source of truth and does not load weights into memory.
    """

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()

    def check_model_installed(self, model_id: str) -> bool:
        """
        Check if the model is registered and installed in the repository.
        """
        model = self.repository.get_model(model_id)
        if not model:
            return False
        return bool(model.get("installed", False))

    def get_model_path(self, model_id: str) -> str | None:
        """
        Retrieve the absolute local folder/file path of the installed model.
        """
        model = self.repository.get_model(model_id)
        if not model or not model.get("installed", False):
            return None
        return model.get("path")

    def get_model_files(self, model_id: str) -> list[str]:
        """
        Scan and retrieve all files belonging to the model weights package directory.
        """
        path_str = self.get_model_path(model_id)
        if not path_str:
            return []
            
        p = Path(path_str)
        if not p.exists():
            return []
            
        if p.is_file():
            return [str(p.resolve())]
        elif p.is_dir():
            try:
                return [str(f.resolve()) for f in p.rglob("*") if f.is_file()]
            except Exception as e:
                logger.error(f"Error scanning directory '{path_str}': {e}")
                return []
        return []

    def build_model_load_plan(self, model_id: str) -> ModelLoadPlan | None:
        """
        Compiles a non-executable step-by-step loading plan containing files, paths, and target backend.
        """
        model = self.repository.get_model(model_id)
        if not model or not model.get("installed", False):
            return None
            
        path = model.get("path", "")
        backend = model.get("recommended_backend") or model.get("backend") or "Unknown"
        files = self.get_model_files(model_id)
        
        # Build non-executable plan steps
        steps = [
            f"1. Locate model weights package at '{path}'",
            f"2. Scan package file tree (found {len(files)} files)",
        ]
        
        if "qnn" in backend.lower() or "npu" in backend.lower():
            steps.extend([
                "3. Allocate Snapdragon HTP execution context",
                "4. Load serialized QNN System and HTP runtime libraries",
                "5. Map model weight tensors into Hexagon NPU memory buffers"
            ])
        elif "onnx" in backend.lower():
            steps.extend([
                "3. Instantiate ONNX Runtime InferenceSession",
                "4. Bind CPU/DirectML execution providers",
                "5. Map ONNX model nodes into compute memory"
            ])
        else:
            steps.extend([
                "3. Allocate host CPU memory buffer",
                "4. Map standard model weights array into RAM",
                "5. Configure CPU execution threads"
            ])
            
        steps.append("6. Signal generation pipeline ready for inference")
        
        return {
            "model_id": model_id,
            "model_path": path,
            "files": files,
            "backend": backend,
            "steps": steps
        }

    def resolve_model(self, model_id: str) -> ModelResolveResult:
        """
        Validates the model installation, resolves file paths, and compiles the load plan.
        Does not load model weights into RAM.
        """
        model = self.repository.get_model(model_id)
        if not model:
            return ModelResolveResult(
                success=False,
                model_id=model_id,
                message=f"Model '{model_id}' is not registered in the repository."
            )

        if not model.get("installed", False):
            return ModelResolveResult(
                success=False,
                model_id=model_id,
                backend=model.get("recommended_backend") or model.get("backend") or "Unknown",
                message="Model is not installed."
            )

        path_str = model.get("path")
        if not path_str:
            return ModelResolveResult(
                success=False,
                model_id=model_id,
                backend=model.get("recommended_backend") or model.get("backend") or "Unknown",
                message="Model installation path is empty."
            )

        p = Path(path_str)
        if not p.exists():
            return ModelResolveResult(
                success=False,
                model_id=model_id,
                backend=model.get("recommended_backend") or model.get("backend") or "Unknown",
                message=f"Model files not found at installed location: '{path_str}'"
            )

        files = self.get_model_files(model_id)
        warnings = []
        if not files:
            warnings.append(f"Model path exists but contains no files.")

        backend = model.get("recommended_backend") or model.get("backend") or "Unknown"

        return ModelResolveResult(
            success=True,
            model_id=model_id,
            model_path=path_str,
            files=files,
            backend=backend,
            message="Model resolved successfully.",
            warnings=warnings
        )
