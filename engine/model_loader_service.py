from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import Condition, RLock
from typing import Any, Iterator, TypedDict

from controllers.model_repository import ModelRepository
from engine.error_diagnostics import diagnose_exception
from engine.logging_config import get_logger
from engine.model_registry import ModelHealthStatus
from engine.performance_metrics import PerformanceOperation, measured
from engine.runtime_model import RuntimeModel

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


class ModelLoadState(str, Enum):
    UNLOADED = "UNLOADED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    UNLOADING = "UNLOADING"
    FAILED = "FAILED"


@dataclass
class LoadedModel:
    model_id: str
    runtime_model: RuntimeModel
    backend_adapter: Any
    references: int = 1


@dataclass
class ModelLoadResult:
    success: bool
    model_id: str
    state: ModelLoadState
    message: str
    loaded_model: LoadedModel | None = None
    reused: bool = False


class ModelLoaderService:
    """
    Foundation service for resolving and loading installed model metadata.
    Uses ModelRepository as the source of truth and does not load weights into memory.
    """

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self.repository = repository or ModelRepository()
        self._condition = Condition(RLock())
        self._state = ModelLoadState.UNLOADED
        self._loaded: LoadedModel | None = None
        self._last_error: str | None = None

    @property
    def state(self) -> ModelLoadState:
        with self._condition:
            return self._state

    @property
    def loaded_model_id(self) -> str | None:
        with self._condition:
            return self._loaded.model_id if self._loaded else None

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

        validation = self.repository.validate_model_installation(model_id)
        if validation is None:
            return ModelResolveResult(
                success=False,
                model_id=model_id,
                message="Model registry validation is unavailable.",
            )
        if validation.status == ModelHealthStatus.INVALID:
            return ModelResolveResult(
                success=False,
                model_id=model_id,
                backend=model.get("recommended_backend") or model.get("backend") or "Unknown",
                message="Model installation is invalid: " + "; ".join(validation.messages),
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

    @measured(
        PerformanceOperation.MODEL_LOAD,
        tags=lambda self, model_id, backend_manager=None: {"model_id": model_id},
        success=lambda result: result.success,
    )
    def load_model(self, model_id: str, backend_manager: Any = None) -> ModelLoadResult:
        """Atomically resolve and initialize one model/backend combination."""
        with self._condition:
            while self._state in (ModelLoadState.LOADING, ModelLoadState.UNLOADING):
                self._condition.wait()

            if self._loaded and self._loaded.model_id == model_id:
                self._loaded.references += 1
                return ModelLoadResult(
                    True,
                    model_id,
                    ModelLoadState.LOADED,
                    "Model is already loaded; existing runtime reused.",
                    self._loaded,
                    reused=True,
                )
            if self._loaded is not None:
                return ModelLoadResult(
                    False,
                    model_id,
                    self._state,
                    f"Model '{self._loaded.model_id}' is still loaded.",
                )
            self._state = ModelLoadState.LOADING
            self._last_error = None

        adapter = None
        try:
            resolve_result = self.resolve_model(model_id)
            if not resolve_result.success:
                raise RuntimeError(resolve_result.message)

            if backend_manager is None:
                from engine.backends.backend_manager import BackendManager

                backend_manager = BackendManager()
            adapter = self.repository.resolve_backend(model_id, backend_manager)
            if adapter is None:
                raise RuntimeError("No compatible and available backend was found.")

            supported = adapter.get_supported_models()
            if supported and model_id not in supported:
                logger.warning(
                    "Backend-Kompatibilitätsliste enthält Modell nicht; registriertes Routing bleibt maßgeblich "
                    "| model=%s backend=%s",
                    model_id,
                    adapter.get_backend_name(),
                )

            adapter.initialize()
            load_plan = self.build_model_load_plan(model_id)
            runtime_model = RuntimeModel(
                model_id=resolve_result.model_id,
                model_path=resolve_result.model_path or "",
                files=resolve_result.files,
                backend=resolve_result.backend,
                load_plan=load_plan,
            )
            loaded = LoadedModel(model_id, runtime_model, adapter)
            with self._condition:
                self._loaded = loaded
                self._state = ModelLoadState.LOADED
                self._condition.notify_all()
            logger.info(
                "Modell geladen | model=%s backend=%s files=%s",
                model_id,
                adapter.get_backend_name(),
                len(resolve_result.files),
            )
            return ModelLoadResult(
                True,
                model_id,
                ModelLoadState.LOADED,
                "Model loaded successfully.",
                loaded,
            )
        except Exception as error:
            if adapter is not None:
                try:
                    adapter.shutdown()
                except Exception as cleanup_error:
                    diagnose_exception(
                        logger,
                        cleanup_error,
                        category="model_loading",
                        context="load_failure_cleanup",
                        backend_name=adapter.get_backend_name(),
                    )
            diagnostic = diagnose_exception(
                logger,
                error,
                category="model_loading",
                context="load_model",
                backend_name=adapter.get_backend_name() if adapter else None,
            )
            with self._condition:
                self._loaded = None
                self._state = ModelLoadState.FAILED
                self._last_error = diagnostic.message
                self._condition.notify_all()
            return ModelLoadResult(
                False,
                model_id,
                ModelLoadState.FAILED,
                diagnostic.message,
            )

    @measured(
        PerformanceOperation.RESOURCE_RELEASE,
        tags=lambda self, model_id=None, force=False: {
            "model_id": model_id or self.loaded_model_id or "none",
            "force": force,
        },
        success=bool,
    )
    def unload_model(self, model_id: str | None = None, *, force: bool = False) -> bool:
        """Release a model reference and shut its backend down at the last release."""
        with self._condition:
            while self._state in (ModelLoadState.LOADING, ModelLoadState.UNLOADING):
                self._condition.wait()
            loaded = self._loaded
            if loaded is None:
                self._state = ModelLoadState.UNLOADED
                return True
            if model_id is not None and loaded.model_id != model_id:
                return False
            if loaded.references > 1 and not force:
                loaded.references -= 1
                return True
            self._state = ModelLoadState.UNLOADING

        success = True
        try:
            loaded.backend_adapter.shutdown()
        except Exception as error:
            success = False
            diagnose_exception(
                logger,
                error,
                category="model_loading",
                context="unload_model",
                backend_name=loaded.backend_adapter.get_backend_name(),
            )
        finally:
            with self._condition:
                self._loaded = None
                self._state = ModelLoadState.UNLOADED
                self._condition.notify_all()
        logger.info("Modell entladen | model=%s", loaded.model_id)
        return success

    def switch_model(
        self, model_id: str, backend_manager: Any = None
    ) -> ModelLoadResult:
        """Switch models without leaving stale resources after a failed load."""
        with self._condition:
            current_id = self._loaded.model_id if self._loaded else None
            references = self._loaded.references if self._loaded else 0
        if current_id == model_id:
            return self.load_model(model_id, backend_manager)
        if references > 1:
            return ModelLoadResult(
                False,
                model_id,
                ModelLoadState.LOADED,
                f"Model '{current_id}' is still in use.",
            )
        if current_id is not None and not self.unload_model(current_id):
            return ModelLoadResult(
                False,
                model_id,
                ModelLoadState.FAILED,
                f"Model '{current_id}' could not be unloaded safely.",
            )
        return self.load_model(model_id, backend_manager)

    @contextmanager
    def model_session(
        self, model_id: str, backend_manager: Any = None
    ) -> Iterator[LoadedModel]:
        """Acquire a loaded model and guarantee release on success, failure, or cancellation."""
        result = self.load_model(model_id, backend_manager)
        if not result.success or result.loaded_model is None:
            raise RuntimeError(result.message)
        try:
            yield result.loaded_model
        finally:
            self.unload_model(model_id)
