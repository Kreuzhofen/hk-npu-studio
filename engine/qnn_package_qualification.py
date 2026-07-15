from __future__ import annotations

import ctypes
import json
import os
import platform
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from controllers.model_repository import ModelCapabilities
from engine.model_install_service import ModelInstallService
from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector
from engine.onnx_provider_service import OnnxProviderService
from engine.package_catalog_service import PackageCatalogService


SCHEMA_VERSION = "1.0.0"
DEFAULT_COMPONENT_PARSE_LIMIT_BYTES = 64 * 1024 * 1024
DEFAULT_BUILD_LIMIT_BYTES = 64 * 1024 * 1024
DEFAULT_FP32_LARGE_LIMIT_BYTES = 1024 * 1024 * 1024
DEFAULT_BUILD_RAM_MULTIPLIER = 6
REQUIRED_DIFFUSION_COMPONENTS = ("tokenizer", "text_encoder", "unet", "vae_decoder", "scheduler")


class QualificationStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    CONDITIONALLY_QUALIFIED = "CONDITIONALLY_QUALIFIED"
    REJECTED = "REJECTED"
    INCOMPLETE = "INCOMPLETE"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    component: str
    description: str
    recommended_action: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _memory_snapshot() -> dict[str, int | None]:
    if os.name != "nt":
        return {"total_physical_bytes": None, "available_physical_bytes": None, "process_working_set_bytes": None}

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong), ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    class ProcessMemory(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("page_fault_count", ctypes.c_ulong),
            ("peak_working_set_size", ctypes.c_size_t), ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t), ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t), ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t), ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    process = ProcessMemory()
    process.cb = ctypes.sizeof(process)
    try:
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(process), process.cb
        )
        return {
            "total_physical_bytes": int(status.total_physical),
            "available_physical_bytes": int(status.available_physical),
            "process_working_set_bytes": int(process.working_set_size),
        }
    except Exception:
        return {"total_physical_bytes": None, "available_physical_bytes": None, "process_working_set_bytes": None}


class QnnPackageQualifier:
    """Headless, conservative qualification gate for local QNN model packages."""

    def __init__(
        self,
        *,
        parse_limit_bytes: int = DEFAULT_COMPONENT_PARSE_LIMIT_BYTES,
        build_limit_bytes: int = DEFAULT_BUILD_LIMIT_BYTES,
        fp32_large_limit_bytes: int = DEFAULT_FP32_LARGE_LIMIT_BYTES,
        strict_loader: Callable[[Path, str], Any] | None = None,
        timestamp_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self.parse_limit_bytes = parse_limit_bytes
        self.build_limit_bytes = build_limit_bytes
        self.fp32_large_limit_bytes = fp32_large_limit_bytes
        self.strict_loader = strict_loader or (
            lambda path, name: OnnxProviderService.create_qnn_strict_session(
                path, name, disable_cpu_fallback=True, enable_basic_profiling=False
            )
        )
        self.timestamp_factory = timestamp_factory or (lambda: datetime.now(timezone.utc))

    @staticmethod
    def _add(
        findings: list[Finding], code: str, severity: str, component: str,
        description: str, action: str,
    ) -> None:
        findings.append(Finding(code, severity, component, description, action))

    @staticmethod
    def _relative(path: Path, package_root: Path) -> str:
        try:
            return path.resolve().relative_to(package_root.resolve()).as_posix()
        except ValueError:
            return path.name

    @staticmethod
    def _pipeline_type(manifest: dict[str, Any]) -> str:
        source = str(manifest.get("source_layout", "")).lower()
        model_id = str(manifest.get("model_id", "")).lower()
        if "xl" in source or "sdxl" in model_id:
            return "stable_diffusion_xl"
        if "stable_diffusion" in model_id or manifest.get("capabilities", {}).get("txt2img"):
            return "stable_diffusion"
        return str(manifest.get("pipeline_type") or manifest.get("package_type") or "unknown")

    def _runtime_package(self, root: Path, manifest: dict[str, Any]) -> ModelRuntimePackage:
        components = manifest.get("components", {}) if isinstance(manifest.get("components"), dict) else {}
        paths: dict[str, str] = {}
        runtimes: dict[str, str] = {}
        for name, config in sorted(components.items()):
            if isinstance(config, dict):
                relative = str(config.get("path", ""))
                paths[name] = str(root / relative) if relative else ""
                runtimes[name] = str(config.get("runtime", ""))
        return ModelRuntimePackage(
            model_id=ModelInstallService._manifest_model_id(manifest),
            base_path=root,
            capabilities=ModelCapabilities(manifest.get("capabilities", {})),
            component_paths=paths,
            component_runtimes=runtimes,
            package_version=ModelInstallService._manifest_version(manifest),
            author=str(manifest.get("author", "")),
            display_name=str(manifest.get("display_name", "")),
        )

    def inspect(self, package_path: str | Path, *, timestamp: str | None = None) -> dict[str, Any]:
        root = Path(package_path).resolve()
        manifest_findings: list[Finding] = []
        static_findings: list[Finding] = []
        components_out: list[dict[str, Any]] = []
        evidence: dict[str, Any] = {
            "static_precheck_passed": False,
            "strict_load_attempted": False,
            "qnn_execution_performed": False,
            "htp_inference_proven": False,
            "compile_attempted": False,
            "large_weight_data_fully_loaded": False,
        }
        before_memory = _memory_snapshot()
        manifest: dict[str, Any] = {}
        manifest_path = root / "package.json"
        if not root.is_dir():
            self._add(manifest_findings, "PACKAGE_PATH_INVALID", "ERROR", "package", "Package path is not a directory.", "Provide an unpacked local package directory.")
        elif not manifest_path.is_file():
            self._add(manifest_findings, "MANIFEST_MISSING", "ERROR", "package", "Required package.json is missing.", "Add a valid package manifest.")
        else:
            try:
                loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("manifest root is not an object")
                manifest = loaded
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
                self._add(manifest_findings, "MANIFEST_UNREADABLE", "ERROR", "package", f"Manifest cannot be read: {exc}", "Repair or recreate package.json.")

        package_id = ModelInstallService._manifest_model_id(manifest)
        package_version = ModelInstallService._manifest_version(manifest)
        if manifest and not package_id:
            self._add(manifest_findings, "MANIFEST_ID_MISSING", "ERROR", "package", "Manifest has no package identity.", "Declare model_id or package_id.")
        if manifest and not package_version:
            self._add(manifest_findings, "MANIFEST_VERSION_MISSING", "ERROR", "package", "Manifest has no version.", "Declare package_version.")
        component_config = manifest.get("components")
        if manifest and not isinstance(component_config, dict):
            self._add(manifest_findings, "MANIFEST_COMPONENTS_INVALID", "ERROR", "package", "Manifest components must be an object.", "Declare component paths and runtimes.")
            component_config = {}
        component_config = component_config or {}
        runtime_package = self._runtime_package(root, manifest)
        qnn_declared = bool(manifest.get("capabilities", {}).get("qnn_runtime"))

        for required in REQUIRED_DIFFUSION_COMPONENTS:
            if required not in component_config:
                self._add(static_findings, "REQUIRED_COMPONENT_MISSING", "ERROR", required, f"Required component '{required}' is not declared.", "Add the required component and manifest entry.")

        total_bytes = 0
        external_bytes = 0
        external_paths_seen: set[Path] = set()
        dynamic_detected = False
        fp32_large_detected = False
        qnn_components = 0
        valid_contexts = 0
        for name, config in sorted(component_config.items()):
            if not isinstance(config, dict):
                self._add(manifest_findings, "MANIFEST_COMPONENT_INVALID", "ERROR", name, "Component declaration is not an object.", "Replace it with path/runtime metadata.")
                continue
            raw_path = str(config.get("path", "")).strip()
            runtime = str(config.get("runtime", "")).upper()
            path = root / raw_path if raw_path else root / "__missing__"
            try:
                path.resolve().relative_to(root)
            except ValueError:
                self._add(static_findings, "COMPONENT_PATH_UNSAFE", "ERROR", name, f"Component path escapes the package: {raw_path}.", "Use a package-relative path without parent traversal.")
                components_out.append({"name": name, "path": raw_path, "runtime": runtime, "exists": False})
                continue
            if not raw_path or not path.exists():
                self._add(static_findings, "REQUIRED_COMPONENT_FILE_MISSING" if name in REQUIRED_DIFFUSION_COMPONENTS else "COMPONENT_FILE_MISSING", "ERROR" if name in REQUIRED_DIFFUSION_COMPONENTS else "WARNING", name, f"Declared component path is missing: {raw_path or '<empty>'}.", "Restore the file/directory or correct the manifest path.")
                components_out.append({"name": name, "path": raw_path, "runtime": runtime, "exists": False})
                continue
            if path.is_dir():
                size = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
                total_bytes += size
                components_out.append({"name": name, "path": raw_path, "runtime": runtime, "exists": True, "kind": "directory", "size_bytes": size})
                continue
            analysis = OnnxComponentInspector.inspect_static(name, path, parse_limit_bytes=self.parse_limit_bytes)
            analysis["path"] = self._relative(path, root)
            analysis["name"] = name
            analysis["runtime"] = runtime
            total_bytes += int(analysis["size_bytes"])
            if not analysis["readable"] or analysis["error"]:
                self._add(static_findings, "COMPONENT_UNREADABLE", "ERROR", name, f"Component is damaged or unreadable: {analysis['error']}", "Replace the component with a validated artifact.")
            for entry in analysis["external_data"]:
                location = str(entry.get("location", ""))
                external_path = path.parent / location
                exists = external_path.is_file()
                entry["exists"] = exists
                entry["path"] = self._relative(external_path, root)
                size = external_path.stat().st_size if exists else 0
                entry["file_size_bytes"] = size
                resolved_external = external_path.resolve()
                if resolved_external not in external_paths_seen:
                    external_bytes += size
                    external_paths_seen.add(resolved_external)
                if not exists:
                    self._add(static_findings, "EXTERNAL_DATA_MISSING", "ERROR", name, f"External tensor data is missing: {location}.", "Restore the external data file.")
            dynamic = any(item["dynamic_dimensions"] for item in analysis["inputs"] + analysis["outputs"])
            if dynamic:
                dynamic_detected = True
                severity = "ERROR" if name == "unet" else "WARNING"
                self._add(static_findings, "REQUIRED_STATIC_SHAPE_MISSING" if severity == "ERROR" else "DYNAMIC_DIMENSION", severity, name, "ONNX contract contains dynamic dimensions.", "Export fixed production shapes for QNN qualification.")
            fp32 = "FLOAT" in analysis["initializer_dtypes"] or any(item["dtype"] == "FLOAT" for item in analysis["inputs"] + analysis["outputs"])
            related_size = int(analysis["size_bytes"]) + sum(int(item.get("file_size_bytes", 0)) for item in analysis["external_data"])
            if fp32 and related_size >= self.fp32_large_limit_bytes:
                fp32_large_detected = True
                self._add(static_findings, "UNREALISTIC_FP32_LARGE_MODEL", "ERROR", name, "FP32 model footprint exceeds 1 GiB and is unsafe for a 16-GB production target.", "Quantize and compile the component offline into validated QNN contexts.")
            ep_nodes = analysis["epcontext_nodes"]
            if runtime == "QNN":
                qnn_components += 1
                if not ep_nodes:
                    self._add(static_findings, "QNN_CONTEXT_MISSING", "ERROR", name, "QNN component has no EPContext wrapper.", "Provide an external QNN context and EPContext wrapper.")
            if ep_nodes:
                if analysis["non_epcontext_nodes"]:
                    self._add(static_findings, "EPCONTEXT_CPU_NODES_PRESENT", "ERROR", name, "EPContext wrapper contains productive non-EPContext nodes.", "Rebuild a pure QNN EPContext wrapper without CPU graph nodes.")
                contexts_ok = True
                for node in ep_nodes:
                    attrs = node["attributes"]
                    ref = str(attrs.get("ep_cache_context", ""))
                    ref_path = Path(ref.replace("\\", "/"))
                    safe = bool(ref) and not ref_path.is_absolute() and ".." not in ref_path.parts
                    context_path = path.parent / ref_path if safe else path.parent / "__invalid__"
                    exists = safe and context_path.is_file() and context_path.stat().st_size > 0
                    node["context_path"] = self._relative(context_path, root) if safe else ref
                    node["context_exists"] = exists
                    if not exists:
                        contexts_ok = False
                        self._add(static_findings, "QNN_CONTEXT_MISSING", "ERROR", name, f"External QNN context is missing or unsafe: {ref or '<empty>'}.", "Restore a non-empty package-relative context binary.")
                if contexts_ok:
                    valid_contexts += 1
            components_out.append(analysis)

        if qnn_declared and qnn_components == 0:
            self._add(manifest_findings, "QNN_MANIFEST_RUNTIME_CONTRADICTION", "ERROR", "package", "qnn_runtime=true but no component declares runtime QNN.", "Align manifest runtimes with the QNN package artifacts.")
        if qnn_declared and valid_contexts < qnn_components:
            self._add(manifest_findings, "QNN_ONLY_CONTEXTS_INCOMPLETE", "ERROR", "package", "QNN runtime is declared but productive contexts are incomplete.", "Supply all required EPContext wrappers and contexts.")
        if not qnn_declared:
            self._add(static_findings, "QNN_RUNTIME_NOT_DECLARED", "WARNING", "package", "Package explicitly does not declare QNN runtime support.", "Use a qualified QNN package for NPU production.")
            if manifest.get("capabilities", {}).get("txt2img") and valid_contexts == 0:
                self._add(static_findings, "PRODUCTIVE_QNN_CONTEXTS_MISSING", "WARNING", "package", "No productive EPContext wrappers and external QNN contexts were found.", "Provide qualified QNN contexts before NPU product use.")
            if qnn_components:
                self._add(manifest_findings, "QNN_COMPONENT_RUNTIME_CONTRADICTION", "ERROR", "package", "Components declare QNN runtime while qnn_runtime=false.", "Align the capability declaration with component runtimes.")

        catalog = PackageCatalogService().get_package(package_id) if package_id else None
        if catalog and str(catalog.get("version", "")) not in {"", package_version}:
            self._add(manifest_findings, "CATALOG_VERSION_MISMATCH", "WARNING", "package", "Package version differs from the local catalog entry.", "Reconcile package and catalog versions.")

        all_findings = manifest_findings + static_findings
        hard_errors = [item for item in all_findings if item.severity == "ERROR"]
        evidence["static_precheck_passed"] = not hard_errors and qnn_declared and qnn_components > 0 and valid_contexts == qnn_components
        status = QualificationStatus.REJECTED if hard_errors else QualificationStatus.INCOMPLETE
        if evidence["static_precheck_passed"]:
            status = QualificationStatus.CONDITIONALLY_QUALIFIED
        elif not manifest:
            status = QualificationStatus.ERROR
        after_memory = _memory_snapshot()
        available = before_memory["available_physical_bytes"]
        total_physical = before_memory["total_physical_bytes"]
        peak_working = max(int(before_memory["process_working_set_bytes"] or 0), int(after_memory["process_working_set_bytes"] or 0))
        risk = "high" if total_bytes + external_bytes >= 8 * 1024**3 or fp32_large_detected else "moderate" if total_bytes + external_bytes >= 2 * 1024**3 else "low"
        report = {
            "schema_version": SCHEMA_VERSION,
            "timestamp": timestamp or self.timestamp_factory().isoformat(),
            "package": {
                "path": root.name,
                "model_id": package_id,
                "version": package_version,
                "type": str(manifest.get("package_type", "")),
                "display_name": str(manifest.get("display_name", "")),
                "qnn_runtime_declared": qnn_declared,
                "declared_resolutions": manifest.get("resolutions", manifest.get("supported_resolutions", [])),
            },
            "pipeline_type": self._pipeline_type(manifest),
            "host_environment": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(), "python": platform.python_version()},
            "runtime_environment": {"qnn_checked": False, "available_providers": [], "provider_registration_status": "not_checked"},
            "components": components_out,
            "manifest_findings": [item.to_dict() for item in manifest_findings],
            "static_findings": [item.to_dict() for item in static_findings],
            "runtime_findings": [],
            "memory_assessment": {
                "declared_package_bytes": total_bytes + external_bytes,
                "onnx_component_bytes": total_bytes,
                "external_data_bytes": external_bytes,
                "available_physical_bytes_at_start": available,
                "total_physical_bytes": total_physical,
                "observed_process_working_set_upper_bound_bytes": peak_working,
                "risk": risk,
                "sixteen_gb_target_risk": risk == "high",
            },
            "qualification_status": status.value,
            "rejection_reasons": [item.code for item in hard_errors],
            "warnings": [item.code for item in all_findings if item.severity == "WARNING"],
            "recommended_actions": sorted({item.recommended_action for item in all_findings}),
            "evidence": evidence,
            "build_assessment": {"requested": False, "permitted": False, "reason": "build_not_requested"},
        }
        return report

    def qualify(
        self,
        package_path: str | Path,
        *,
        strict: bool = True,
        allow_build: bool = False,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        report = self.inspect(package_path, timestamp=timestamp)
        report["build_assessment"] = self._build_assessment(report, allow_build)
        if not strict or not report["evidence"]["static_precheck_passed"]:
            return report
        report["evidence"]["strict_load_attempted"] = True
        diagnostics = OnnxProviderService.diagnostics()
        report["runtime_environment"] = {
            "qnn_checked": True,
            "available_providers": diagnostics.get("available_providers", []),
            "provider_registration_status": diagnostics.get("provider_registration_status", "unknown"),
        }
        failures = 0
        successes = 0
        for component in report["components"]:
            if component.get("runtime") != "QNN" or not component.get("epcontext_nodes"):
                continue
            name = str(component["name"])
            path = Path(package_path).resolve() / str(component["path"])
            try:
                session = self.strict_loader(path, name)
                providers = OnnxProviderService.session_providers(session)
                if OnnxProviderService.QNN_PROVIDER not in providers:
                    raise RuntimeError(f"Unexpected strict providers: {providers}")
                successes += 1
                report["runtime_findings"].append(Finding("STRICT_QNN_LOAD_PASSED", "INFO", name, "Strict QNN session loaded with CPU fallback disabled.", "Retain this wrapper/context pair as qualification evidence.").to_dict())
                runtime_memory = _memory_snapshot()
                report["memory_assessment"]["observed_process_working_set_upper_bound_bytes"] = max(
                    int(report["memory_assessment"]["observed_process_working_set_upper_bound_bytes"]),
                    int(runtime_memory["process_working_set_bytes"] or 0),
                )
                del session
            except Exception as exc:
                failures += 1
                report["runtime_findings"].append(Finding("STRICT_QNN_LOAD_FAILED", "ERROR", name, f"Strict load without CPU fallback failed: {exc}", "Rebuild or replace the incompatible QNN context.").to_dict())
        if failures:
            report["qualification_status"] = QualificationStatus.REJECTED.value
            report["rejection_reasons"].append("STRICT_QNN_LOAD_FAILED")
            report["recommended_actions"] = sorted(set(report["recommended_actions"] + ["Rebuild or replace the incompatible QNN context."]))
        elif successes:
            report["qualification_status"] = QualificationStatus.CONDITIONALLY_QUALIFIED.value
        else:
            report["qualification_status"] = QualificationStatus.INCOMPLETE.value
        report["evidence"]["strict_load_passed_components"] = successes
        report["evidence"]["strict_load_failed_components"] = failures
        return report

    def _build_assessment(self, report: dict[str, Any], requested: bool) -> dict[str, Any]:
        candidates = [item for item in report["components"] if item.get("kind") != "directory" and item.get("runtime") != "QNN"]
        largest = max((int(item.get("size_bytes", 0)) for item in candidates), default=0)
        available = int(report["memory_assessment"].get("available_physical_bytes_at_start") or 0)
        required = largest * DEFAULT_BUILD_RAM_MULTIPLIER
        if not requested:
            reason = "build_not_requested"
        elif not report["evidence"]["static_precheck_passed"]:
            reason = "static_precheck_failed"
        elif largest > self.build_limit_bytes:
            reason = "component_exceeds_build_size_limit"
        elif not available or available < required:
            reason = "insufficient_free_ram"
        else:
            reason = "no_safe_additional_evidence_defined"
        return {"requested": requested, "permitted": False, "reason": reason, "largest_candidate_bytes": largest, "size_limit_bytes": self.build_limit_bytes, "required_free_ram_bytes": required, "available_free_ram_bytes": available}


def deterministic_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
