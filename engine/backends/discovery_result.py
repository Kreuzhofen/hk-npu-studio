from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiscoveryResult:
    """
    Data class representing the detected system environment and available hardware acceleration backends.
    Used for displaying system health, SDK presence, and selecting backends without UI dependencies.
    """
    os_name: str
    os_version: str
    architecture: str
    python_version: str
    is_windows_arm64: bool
    
    cpu_available: bool = True
    onnx_available: bool = False
    onnx_version: str | None = None
    
    qnn_sdk_found: bool = False
    qnn_sdk_path: str | None = None
    qnn_tools_found: bool = False
    qnn_net_run_path: str | None = None
    qnn_htp_backend_path: str | None = None
    qnn_htp_skeleton_dirs: tuple[str, ...] = ()
    
    available_backends: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
