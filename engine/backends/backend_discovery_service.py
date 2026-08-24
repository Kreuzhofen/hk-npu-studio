from __future__ import annotations

import os
import platform
import re
from pathlib import Path
from engine.backends.discovery_result import DiscoveryResult


class BackendDiscoveryService:
    """
    Scans local operating system environment properties, Python runtimes,
    ONNX Runtime libraries, and Qualcomm SDK paths to discover available hardware backends.
    Avoids loading hardware driver binaries directly to remain thread-safe.
    """

    TYPICAL_QNN_PATHS = [
        r"C:\Qualcomm\AIStack",
        r"C:\Qualcomm\AIEngineDirect",
        r"C:\Qualcomm\AIStack\QAIRT",
    ]

    ENV_QNN_VARS = [
        "QNN_SDK_ROOT",
        "QNN_SDK_PATH",
        "QUALCOMM_AI_ENGINE_DIRECT_SDK",
        "QAIRT_SDK_ROOT"
    ]

    @classmethod
    def discover(cls) -> DiscoveryResult:
        """Scan system and environment paths to compile a DiscoveryResult."""
        os_name = platform.system()
        os_version = platform.version()
        
        # Check architecture safely, accounts for potential emulation layers
        raw_machine = platform.machine().upper()
        env_arch = os.environ.get("PROCESSOR_ARCHITECTURE", "").upper()
        if "ARM64" in raw_machine or "ARM64" in env_arch or "AARCH64" in raw_machine:
            architecture = "ARM64"
        else:
            architecture = raw_machine if raw_machine else "x86_64"

        is_windows_arm64 = (os_name == "Windows" and architecture == "ARM64")
        python_version = platform.python_version()

        cpu_available = True
        onnx_available = False
        onnx_version = None
        warnings = []
        errors = []

        # 1. Discover ONNX Runtime
        try:
            import onnxruntime
            onnx_available = True
            onnx_version = onnxruntime.__version__
        except ImportError:
            warnings.append("onnxruntime Python-Bibliothek ist nicht installiert.")

        # 2. Discover Qualcomm QNN SDK
        qnn_sdk_found = False
        qnn_sdk_path = None
        qnn_tools_found = False
        qnn_net_run_path = None
        qnn_htp_backend_path = None
        qnn_htp_skeleton_dirs: tuple[str, ...] = ()

        # Check environment variables first
        for var_name in cls.ENV_QNN_VARS:
            val = os.environ.get(var_name)
            if val:
                path = Path(val)
                if path.exists() and path.is_dir():
                    qnn_sdk_found = True
                    qnn_sdk_path = str(path.resolve())
                    break

        # Check typical paths if not found via env variables
        if not qnn_sdk_found:
            for typical_path in cls.TYPICAL_QNN_PATHS:
                p = Path(typical_path)
                if p.exists() and p.is_dir():
                    # Direct check if this path has bin/
                    if (p / "bin").exists():
                        qnn_sdk_found = True
                        qnn_sdk_path = str(p.resolve())
                        break
                    
                    # Search one level deep (e.g. for versions inside AIStack/QAIRT)
                    try:
                        subdirs = [x for x in p.iterdir() if x.is_dir()]
                        for subdir in subdirs:
                            if (subdir / "bin").exists() or (subdir / "qairt").exists():
                                qnn_sdk_found = True
                                qnn_sdk_path = str(subdir.resolve())
                                break
                    except Exception:
                        pass
                    
                    if qnn_sdk_found:
                        break

        # Search for qnn-net-run.exe tool binary inside QNN SDK directory
        if qnn_sdk_path:
            sdk_p = Path(qnn_sdk_path)
            search_patterns = [
                "bin/aarch64-windows/qnn-net-run.exe",
                "bin/aarch64-windows-msvc/qnn-net-run.exe",
                "bin/x86_64-windows/qnn-net-run.exe",
                "bin/x86_64-windows-msvc/qnn-net-run.exe",
                "qairt/bin/aarch64-windows/qnn-net-run.exe",
                "qairt/bin/x86_64-windows/qnn-net-run.exe",
            ]
            for pattern in search_patterns:
                exe_p = sdk_p / pattern
                if exe_p.exists():
                    qnn_tools_found = True
                    qnn_net_run_path = str(exe_p.resolve())
                    break

            # Fallback recursive search if not found in standard directories
            if not qnn_tools_found:
                try:
                    for root, dirs, files in os.walk(qnn_sdk_path):
                        if "qnn-net-run.exe" in files:
                            qnn_tools_found = True
                            qnn_net_run_path = str(Path(root) / "qnn-net-run.exe")
                            break
                except Exception as error:
                    warnings.append(f"Fehler bei rekursiver qnn-net-run.exe Suche: {error}")

            backend_patterns = [
                "lib/aarch64-windows-msvc/QnnHtp.dll",
                "lib/aarch64-windows/QnnHtp.dll",
                "qairt/lib/aarch64-windows-msvc/QnnHtp.dll",
                "qairt/lib/aarch64-windows/QnnHtp.dll",
            ]
            for pattern in backend_patterns:
                backend_path = sdk_p / pattern
                if backend_path.is_file():
                    qnn_htp_backend_path = str(backend_path.resolve())
                    break
            if qnn_htp_backend_path is None:
                try:
                    for root, dirs, files in os.walk(qnn_sdk_path):
                        if "QnnHtp.dll" in files:
                            qnn_htp_backend_path = str(Path(root) / "QnnHtp.dll")
                            break
                except Exception as error:
                    warnings.append(f"Fehler bei rekursiver QnnHtp.dll Suche: {error}")

            skeleton_dirs = set()
            skeleton_pattern = re.compile(r"^libQnnHtpV(.+)Skel\.so$", re.IGNORECASE)
            try:
                for root, _dirs, files in os.walk(sdk_p):
                    catalog_names = {name.casefold() for name in files}
                    for name in files:
                        match = skeleton_pattern.match(name)
                        if match and (
                            f"libqnnhtpv{match.group(1)}.cat".casefold()
                            in catalog_names
                        ):
                            skeleton_dirs.add(str(Path(root).resolve()))
            except Exception as error:
                warnings.append(f"Fehler bei HTP-Skeleton-Suche: {error}")
            qnn_htp_skeleton_dirs = tuple(
                sorted(skeleton_dirs, key=lambda path: path.casefold())
            )

        # Assemble available backends list
        available_backends = ["CPU"]
        if onnx_available:
            available_backends.append("ONNX Runtime")
        if qnn_sdk_found and qnn_tools_found:
            available_backends.append("Qualcomm QNN NPU")
        else:
            if not qnn_sdk_found:
                warnings.append("Qualcomm QNN SDK wurde nicht im Systempfad gefunden.")
            elif not qnn_tools_found:
                warnings.append("Qualcomm QNN SDK Verzeichnis existiert, aber qnn-net-run.exe fehlt.")

        return DiscoveryResult(
            os_name=os_name,
            os_version=os_version,
            architecture=architecture,
            python_version=python_version,
            is_windows_arm64=is_windows_arm64,
            cpu_available=cpu_available,
            onnx_available=onnx_available,
            onnx_version=onnx_version,
            qnn_sdk_found=qnn_sdk_found,
            qnn_sdk_path=qnn_sdk_path,
            qnn_tools_found=qnn_tools_found,
            qnn_net_run_path=qnn_net_run_path,
            qnn_htp_backend_path=qnn_htp_backend_path,
            qnn_htp_skeleton_dirs=qnn_htp_skeleton_dirs,
            available_backends=available_backends,
            warnings=warnings,
            errors=errors,
        )
