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
        component_runtimes: dict[str, str] | None = None
    ) -> None:
        self.model_id = model_id
        self.base_path = Path(base_path)
        self.capabilities = capabilities
        
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
        
    def to_dict(self) -> dict[str, Any]:
        """
        Serialize metadata for debugging/logging.
        """
        return {
            "model_id": self.model_id,
            "base_path": str(self.base_path.as_posix()),
            "capabilities": self.capabilities.to_dict(),
            "component_paths": self.component_paths,
            "component_runtimes": self.component_runtimes
        }
