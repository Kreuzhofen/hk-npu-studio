from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("OnnxProviderService")


class OnnxProviderService:
    """
    Central ONNX Runtime provider discovery and session factory.
    QNN is optional and CPUExecutionProvider remains the stable fallback.
    """

    QNN_PROVIDER = "QNNExecutionProvider"
    CPU_PROVIDER = "CPUExecutionProvider"
    AI_STACK_ROOT = Path(r"C:\Qualcomm\AIStack\2.47.0.260601")

    _initialized = False
    _registration_attempted = False
    _registration_status = "not_attempted"
    _registration_error: str | None = None
    _providers_before: list[str] = []
    _providers_after: list[str] = []
    _qnn_provider_options: dict[str, Any] = {}
    _dll_directories: list[Any] = []
    _diagnostic_log_dir = Path(r"C:\SnapdragonAI\diagnostics\logs")

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return

        cls._initialized = True
        try:
            import onnxruntime as ort
            cls._providers_before = list(ort.get_available_providers())
        except Exception as exc:
            cls._registration_status = "onnxruntime_unavailable"
            cls._registration_error = str(exc)
            logger.warning("[OnnxProviderService] ONNX Runtime unavailable: %s", exc)
            return

        cls._prepare_qnn_registration()

        try:
            cls._providers_after = list(ort.get_available_providers())
        except Exception as exc:
            cls._providers_after = []
            logger.warning("[OnnxProviderService] Provider query after registration failed: %s", exc)

        logger.info("[OnnxProviderService] Providers before QNN registration: %s", cls._providers_before)
        logger.info("[OnnxProviderService] Providers after QNN registration: %s", cls._providers_after)
        logger.info("[OnnxProviderService] QNN registration status: %s", cls._registration_status)
        print(f"[OnnxProviderService] Providers before QNN registration: {cls._providers_before}")
        print(f"[OnnxProviderService] Providers after QNN registration: {cls._providers_after}")
        print(f"[OnnxProviderService] QNN registration status: {cls._registration_status}")

    @classmethod
    def _prepare_qnn_registration(cls) -> None:
        if cls.QNN_PROVIDER in cls._providers_before:
            cls._registration_status = "already_available"
            cls._qnn_provider_options = cls._build_qnn_provider_options(None)
            return

        cls._registration_attempted = True
        try:
            import onnxruntime as ort
            import onnxruntime_qnn

            qnn_library_path = Path(onnxruntime_qnn.get_library_path())
            qnn_library_dir = qnn_library_path.parent

            cls._add_dll_directory(qnn_library_dir)
            cls._add_dll_directory(cls.AI_STACK_ROOT / "bin" / "aarch64-windows-msvc")
            cls._add_dll_directory(cls.AI_STACK_ROOT / "lib" / "aarch64-windows-msvc")

            ort.register_execution_provider_library(
                onnxruntime_qnn.get_ep_name(),
                str(qnn_library_path),
            )
            cls._qnn_provider_options = cls._build_qnn_provider_options(onnxruntime_qnn)
            cls._registration_status = "registered"
        except ImportError as exc:
            cls._registration_status = "onnxruntime_qnn_missing"
            cls._registration_error = str(exc)
            logger.info("[OnnxProviderService] onnxruntime_qnn not installed: %s", exc)
        except Exception as exc:
            cls._registration_status = "registration_failed"
            cls._registration_error = str(exc)
            logger.warning("[OnnxProviderService] QNN provider registration failed: %s", exc)

    @classmethod
    def _add_dll_directory(cls, path: Path) -> None:
        if not path.exists() or not path.is_dir():
            return

        path_text = str(path)
        os.environ["PATH"] = path_text + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            try:
                cls._dll_directories.append(os.add_dll_directory(path_text))
            except Exception as exc:
                logger.debug("[OnnxProviderService] add_dll_directory skipped for %s: %s", path_text, exc)

    @classmethod
    def _build_qnn_provider_options(cls, onnxruntime_qnn: Any | None) -> dict[str, Any]:
        try:
            if onnxruntime_qnn is not None:
                htp_path = onnxruntime_qnn.get_qnn_htp_path()
            else:
                htp_path = cls.AI_STACK_ROOT / "lib" / "aarch64-windows-msvc" / "QnnHtp.dll"
            if htp_path and Path(htp_path).exists():
                return {"backend_path": str(htp_path)}
        except Exception as exc:
            logger.debug("[OnnxProviderService] QNN provider options unavailable: %s", exc)
        return {}

    @classmethod
    def available_providers(cls) -> list[str]:
        cls.initialize()
        return list(cls._providers_after)

    @classmethod
    def qnn_available(cls) -> bool:
        return cls.QNN_PROVIDER in cls.available_providers()

    @classmethod
    def provider_registration_status(cls) -> str:
        cls.initialize()
        return cls._registration_status

    @classmethod
    def provider_options(cls) -> dict[str, Any]:
        cls.initialize()
        return dict(cls._qnn_provider_options)

    @classmethod
    def preferred_providers(cls) -> list[Any]:
        cls.initialize()
        providers: list[Any] = []
        if cls.QNN_PROVIDER in cls._providers_after:
            options = cls.provider_options()
            providers.append((cls.QNN_PROVIDER, options) if options else cls.QNN_PROVIDER)
        if cls.CPU_PROVIDER in cls._providers_after:
            providers.append(cls.CPU_PROVIDER)
        return providers or [cls.CPU_PROVIDER]

    @classmethod
    def create_session(cls, model_path: str | Path, component_name: str = "onnx"):
        cls.initialize()
        import onnxruntime as ort

        providers = cls.preferred_providers()
        logger.info("[OnnxProviderService] Loading %s with providers: %s", component_name, providers)
        print(f"[OnnxProviderService] Loading {component_name} with providers: {providers}")
        session = ort.InferenceSession(str(model_path), providers=providers)
        logger.info("[OnnxProviderService] %s session providers: %s", component_name, session.get_providers())
        print(f"[OnnxProviderService] {component_name} session providers: {session.get_providers()}")
        return session

    @classmethod
    def create_qnn_strict_session(
        cls,
        model_path: str | Path,
        component_name: str = "qnn_strict",
        disable_cpu_fallback: bool = True,
        enable_basic_profiling: bool = True,
    ):
        cls.initialize()
        import onnxruntime as ort

        options = ort.SessionOptions()
        if disable_cpu_fallback:
            options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")

        provider_options = cls.provider_options()
        profiling_file_path = cls._build_profiling_file_path(component_name, model_path)
        if enable_basic_profiling:
            provider_options["profiling_level"] = "basic"
            provider_options["profiling_file_path"] = str(profiling_file_path)

        logger.info(
            "[OnnxProviderService] Strict QNN load for %s with options: %s",
            component_name,
            provider_options,
        )
        print(f"[OnnxProviderService] Strict QNN load for {component_name} with options: {provider_options}")
        explicit_devices = []
        if hasattr(ort, "get_ep_devices") and hasattr(options, "add_provider_for_devices"):
            explicit_devices = [
                device for device in ort.get_ep_devices()
                if getattr(device, "ep_name", "") == cls.QNN_PROVIDER
            ]
        if explicit_devices:
            options.add_provider_for_devices(explicit_devices, provider_options)
            session = ort.InferenceSession(str(model_path), sess_options=options)
        else:
            session = ort.InferenceSession(
                str(model_path),
                sess_options=options,
                providers=[cls.QNN_PROVIDER],
                provider_options=[provider_options],
            )
        logger.info("[OnnxProviderService] Strict QNN %s session providers: %s", component_name, session.get_providers())
        print(f"[OnnxProviderService] Strict QNN {component_name} session providers: {session.get_providers()}")
        return session

    @classmethod
    def _build_profiling_file_path(cls, component_name: str, model_path: str | Path) -> Path:
        safe_component = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in component_name)
        safe_model = Path(model_path).stem or "model"
        try:
            cls._diagnostic_log_dir.mkdir(parents=True, exist_ok=True)
            return cls._diagnostic_log_dir / f"qnn_{safe_component}_{safe_model}_profile.csv"
        except Exception:
            return Path(os.environ.get("TEMP", ".")) / f"qnn_{safe_component}_{safe_model}_profile.csv"

    @classmethod
    def find_local_qnn_test_candidates(
        cls,
        project_root: str | Path = r"C:\SnapdragonAI",
        max_size_mb: int = 64,
    ) -> list[dict[str, Any]]:
        root = Path(project_root)
        if not root.exists():
            return []

        candidates: list[dict[str, Any]] = []
        for path in root.rglob("*.onnx"):
            try:
                size = path.stat().st_size
            except Exception:
                continue

            lowered = str(path).lower()
            is_placeholder = size <= 1024
            is_sdxl_component = "\\models\\sdxl_base\\" in lowered or "/models/sdxl_base/" in lowered
            if is_placeholder:
                reason = "placeholder_or_invalid"
            elif is_sdxl_component:
                reason = "sdxl_component_not_small_test_model"
            elif size <= max_size_mb * 1024 * 1024:
                reason = "small_onnx_candidate"
            else:
                reason = "too_large_for_diagnostic_smoke_test"

            candidates.append({
                "path": str(path),
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 3),
                "classification": reason,
                "suitable_for_strict_qnn_smoke_test": reason == "small_onnx_candidate",
            })

        return sorted(candidates, key=lambda item: item["size_bytes"])

    @classmethod
    def run_strict_qnn_diagnostic(cls, model_path: str | Path, component_name: str = "qnn_test") -> dict[str, Any]:
        cls.initialize()
        model = Path(model_path)
        result: dict[str, Any] = {
            "model_path": str(model),
            "component_name": component_name,
            "qnn_available": cls.qnn_available(),
            "provider_registration_status": cls.provider_registration_status(),
            "provider_options": cls.provider_options(),
            "disable_cpu_fallback": True,
            "profiling_level": "basic",
            "profiling_file_path": str(cls._build_profiling_file_path(component_name, model)),
            "status": "not_run",
            "classification": "",
            "session_providers": [],
            "error": "",
        }

        if not result["qnn_available"]:
            result["status"] = "provider_unavailable"
            result["classification"] = "Provider-/DLL-/Optionen-Fehler"
            return result

        if not model.exists() or not model.is_file():
            result["status"] = "model_missing"
            result["classification"] = "Testmodell fehlt"
            return result

        try:
            session = cls.create_qnn_strict_session(model, component_name)
            providers = cls.session_providers(session)
            result["session_providers"] = providers
            del session
            if cls.QNN_PROVIDER in providers:
                result["status"] = "qnn_full"
                result["classification"] = "Modell läuft vollständig auf QNN"
            elif cls.CPU_PROVIDER in providers:
                result["status"] = "cpu_fallback"
                result["classification"] = "CPU-Fallback aktiv"
            else:
                result["status"] = "unknown_provider"
                result["classification"] = "Providerstatus unklar"
        except Exception as exc:
            result["status"] = "qnn_incompatible_or_load_failed"
            result["classification"] = "Modell nicht QNN-kompatibel"
            result["error"] = str(exc)

        return result

    @classmethod
    def session_providers(cls, session: Any) -> list[str]:
        try:
            return list(session.get_providers())
        except Exception:
            return []

    @classmethod
    def runtime_label(cls, session_provider_lists: list[list[str]] | None = None) -> str:
        cls.initialize()
        provider_lists = session_provider_lists or []
        flat = [provider for providers in provider_lists for provider in providers]
        if cls.QNN_PROVIDER in flat:
            return "ONNX Runtime QNN Provider"
        if cls.QNN_PROVIDER in cls._providers_after:
            return "QNN available / CPU fallback"
        return "ONNX Runtime CPU"

    @classmethod
    def diagnostics(cls) -> dict[str, Any]:
        cls.initialize()
        return {
            "available_providers_before_registration": list(cls._providers_before),
            "available_providers": list(cls._providers_after),
            "qnn_available": cls.QNN_PROVIDER in cls._providers_after,
            "provider_registration_status": cls._registration_status,
            "provider_registration_error": cls._registration_error,
            "provider_options": cls.provider_options(),
            "ai_stack_root": str(cls.AI_STACK_ROOT),
            "qnn_registration_attempted": cls._registration_attempted,
        }

