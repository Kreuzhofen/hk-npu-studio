from __future__ import annotations
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
        
        # Paths for supported components: tokenizer, text_encoder, text_encoder_2, unet, vae_decoder, scheduler
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
        Validates that all declared paths exist on disk.
        """
        for name, path_str in self.component_paths.items():
            if path_str:
                p = Path(path_str)
                if not p.exists():
                    return False
        return True
        
    def verify_components(self) -> dict[str, str]:
        """
        Verify status of each expected component in the package.
        Returns a dictionary mapping component names to their status:
        - READY: Component exists, is valid type, and is not a mock stub (e.g., size > 1024 bytes).
        - FOUND: Component exists but size check indicates it's a stub or incomplete validation.
        - INVALID: Component exists but fails basic type/size validation.
        - MISSING: Component path is empty or does not exist on disk.
        """
        statuses = {}
        expected_components = ["tokenizer", "text_encoder", "text_encoder_2", "unet", "vae_decoder", "scheduler"]
        
        for name in expected_components:
            path_str = self.component_paths.get(name)
            if not path_str:
                statuses[name] = "MISSING"
                continue
                
            p = Path(path_str)
            if not p.exists():
                statuses[name] = "MISSING"
                continue
                
            # Basic validation
            if name in ["tokenizer", "scheduler"]:
                if p.is_dir():
                    try:
                        children = list(p.iterdir())
                        # If a config or vocab file is in the directory, it's ready.
                        if len(children) > 0:
                            statuses[name] = "READY"
                        else:
                            statuses[name] = "FOUND" # directory exists but is empty
                    except Exception:
                        statuses[name] = "INVALID"
                else:
                    statuses[name] = "INVALID"
            else:
                if p.is_file():
                    # Check file size. Real weights are large. 
                    # If it's a small mock file (<= 1024 bytes), label it as INVALID or FOUND
                    if p.stat().st_size <= 1024:
                        statuses[name] = "FOUND" # Found the stub file, but it's not a real weight
                    else:
                        statuses[name] = "READY"
                else:
                    statuses[name] = "INVALID"
                    
        return statuses

    def is_fully_ready(self) -> bool:
        """
        Checks if all expected components are in the READY status.
        """
        statuses = self.verify_components()
        return all(status == "READY" for status in statuses.values())
        
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
