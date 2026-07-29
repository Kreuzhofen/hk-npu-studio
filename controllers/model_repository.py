from __future__ import annotations

import os
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from config import PREFERENCES_PATH
from app.configuration_manager import ConfigurationManager


class ModelCapabilities:
    """
    Encapsulates capability metadata for a model.
    Provides structured boolean flags for txt2img, img2img, inpainting,
    outpainting, LoRA, ControlNet, Image-to-Video, Batch Generation,
    ONNX Runtime, and QNN Runtime.
    """
    def __init__(self, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        self.txt2img = bool(data.get("txt2img", False))
        self.img2img = bool(data.get("img2img", False))
        self.inpainting = bool(data.get("inpainting", False))
        self.outpainting = bool(data.get("outpainting", False))
        self.lora = bool(data.get("lora", False))
        self.controlnet = bool(data.get("controlnet", False))
        self.image_to_video = bool(data.get("image_to_video", False))
        self.batch_generation = bool(data.get("batch_generation", False))
        self.onnx_runtime = bool(data.get("onnx_runtime", False))
        self.qnn_runtime = bool(data.get("qnn_runtime", False))
        self.qnn_dlc_runtime = bool(data.get("qnn_dlc_runtime", False))

    def has_capability(self, capability: str) -> bool:
        normalized = capability.lower().replace("-", "_").replace(" ", "_")
        return getattr(self, normalized, False)

    def to_dict(self) -> dict[str, bool]:
        return {
            "txt2img": self.txt2img,
            "img2img": self.img2img,
            "inpainting": self.inpainting,
            "outpainting": self.outpainting,
            "lora": self.lora,
            "controlnet": self.controlnet,
            "image_to_video": self.image_to_video,
            "batch_generation": self.batch_generation,
            "onnx_runtime": self.onnx_runtime,
            "qnn_runtime": self.qnn_runtime,
            "qnn_dlc_runtime": self.qnn_dlc_runtime
        }


class ModelRepository:
    """
    Data-driven repository that scans resources/models/*.json files.
    Acting as the Single Source of Truth for model metadata, validating structure,
    and handling updates back to disk.

    Future Roadmap Hooks:
    - Model Download: Downloading large model weights from Hugging Face/API.
    - Model Installation: Unpacking and verify directory placements.
    - Model Update: Checking remote hashes/versions and pull updates.
    - Model Removal: Safely delete weights and configuration files.
    - Repository Refresh: Recan models folder dynamically at runtime.
    - Repository Cache: In-memory serialization cache for fast startup.
    - Signature Verification: Checking GPG/SHA256 signatures to ensure authenticity.
    - Version Management: Resolving version conflicts and upgrade schemas.
    """

    _active_model_id: str | None = None
    _logged_smp_models: set[str] = set()
    _preferences_path: Path = PREFERENCES_PATH

    @classmethod
    def get_active_model_id(cls) -> str | None:
        return cls._active_model_id

    def set_active_model_id(self, model_id: str | None) -> None:
        """Persist a valid selectable model as the shared active model."""
        if model_id is not None and not self.is_selectable_model(model_id):
            return
        ModelRepository._active_model_id = model_id
        self._save_active_model_preference(model_id)

    def __init__(self, models_dir: str | None = None) -> None:
        if models_dir is None:
            # Default to resources/models relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.models_dir = os.path.join(base_dir, "resources", "models")
        else:
            self.models_dir = models_dir

        self._models: dict[str, dict[str, Any]] = {}
        self.load_repository()

    def load_repository(self) -> None:
        """
        Scan directory and load all valid model JSON definitions.
        """
        self._models.clear()
        if not os.path.exists(self.models_dir):
            print(f"[ModelRepository] Warning: Directory {self.models_dir} does not exist.")
            return

        for filename in sorted(os.listdir(self.models_dir)):
            if filename.endswith(".json"):
                filepath = os.path.join(self.models_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if self._validate_model_data(data):
                        model_id = data["id"]
                        # Keep track of file path for updates
                        data["_filepath"] = filepath
                        self._models[model_id] = data
                    else:
                        print(f"[ModelRepository] Error: Validation failed for {filename}")
                except Exception as e:
                    print(f"[ModelRepository] Error loading {filename}: {e}")

        selectable_models = [
            model_id for model_id in self._models if self.is_selectable_model(model_id)
        ]
        active_model = ModelRepository._active_model_id
        if active_model not in selectable_models:
            preferred_model = self._load_active_model_preference()
            active_model = preferred_model if preferred_model in selectable_models else None
            if active_model is None:
                active_model = selectable_models[0] if selectable_models else None
            ModelRepository._active_model_id = active_model
            self._save_active_model_preference(active_model)

    def _validate_model_data(self, data: dict[str, Any]) -> bool:
        """
        Validate required schema fields.
        """
        required_fields = {
            "id", "display_name", "author", "version", "license",
            "description", "category", "backend", "recommended_backend",
            "minimum_ram_gb", "recommended_ram_gb", "supports",
            "installed", "downloaded", "path", "status", "capabilities"
        }
        return required_fields.issubset(data.keys())

    def get_model(self, model_id: str) -> dict[str, Any] | None:
        """
        Retrieve a model definition by ID.
        """
        return self._models.get(model_id)

    def get_all_models(self) -> list[dict[str, Any]]:
        """
        Get all registered models.
        """
        return list(self._models.values())

    def get_product_models(self) -> list[dict[str, Any]]:
        """Return installed product models that are selectable for generation."""
        return [model for model in self._models.values() if self.is_selectable_model(str(model.get("id", "")))]

    def is_product_model(self, model_id: str) -> bool:
        """Whether a model may be selected in a production generation workspace."""
        model = self.get_model(model_id)
        return bool(model and model.get("product_available") is True)

    def is_selectable_model(self, model_id: str) -> bool:
        """Whether an installed product model can be activated for generation."""
        model = self.get_model(model_id)
        return bool(
            model
            and model.get("product_available") is True
            and model.get("installed") is True
            and isinstance(model.get("generation_parameters"), dict)
        )

    @classmethod
    def _load_active_model_preference(cls) -> str | None:
        data = ConfigurationManager(cls._preferences_path).load()
        value = data.get("active_model_id")
        return str(value) if value else None

    @classmethod
    def _save_active_model_preference(cls, model_id: str | None) -> None:
        ConfigurationManager(cls._preferences_path).save(
            {"active_model_id": model_id}
        )

    def get_generation_parameters(self, model_id: str) -> dict[str, Any] | None:
        """Return the model-owned generation control contract, if declared."""
        model = self.get_model(model_id)
        parameters = model.get("generation_parameters") if model else None
        return deepcopy(parameters) if isinstance(parameters, dict) else None

    def validate_generation_parameters(
        self, model_id: str, values: dict[str, Any]
    ) -> tuple[bool, str]:
        """Validate visible generation values against the model-owned contract."""
        contract = self.get_generation_parameters(model_id)
        if not contract:
            return False, f"Kein Generation-Parametervertrag für Modell '{model_id}' gefunden."

        for name, value in values.items():
            spec = contract.get(name)
            if not isinstance(spec, dict):
                continue
            allowed = spec.get("values")
            if isinstance(allowed, list) and allowed and value not in allowed:
                return False, f"{name} wird vom ausgewählten Modell nicht unterstützt: {value}"
            if "min" in spec and value < spec["min"]:
                return False, f"{name} muss mindestens {spec['min']} sein."
            if "max" in spec and value > spec["max"]:
                return False, f"{name} darf höchstens {spec['max']} sein."
            resolution = spec.get("resolution")
            if resolution and "min" in spec:
                offset = (float(value) - float(spec["min"])) / float(resolution)
                if abs(offset - round(offset)) > 1e-9:
                    return False, f"{name} muss dem Raster {resolution} entsprechen."

        return True, "Validierung erfolgreich."

    def update_model(self, model_id: str, **kwargs: Any) -> bool:
        """
        Update model metadata in memory and write changes to the original file.
        """
        model = self._models.get(model_id)
        if not model:
            print(f"[ModelRepository] Error: Model {model_id} not found.")
            return False

        # Update in-memory
        for key, value in kwargs.items():
            if key != "id" and not key.startswith("_"):
                model[key] = value

        # Save to disk
        filepath = model.get("_filepath")
        if not filepath or not os.path.exists(filepath):
            print(f"[ModelRepository] Error: Original file path not found for {model_id}")
            return False

        try:
            # Create a clean dictionary for serializing without private keys
            serializable_data = {k: v for k, v in model.items() if not k.startswith("_")}
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, indent=2)
            return True
        except Exception as e:
            print(f"[ModelRepository] Error saving updates to {filepath}: {e}")
            return False

    def get_model_capabilities(self, model_id: str) -> ModelCapabilities | None:
        """
        Retrieve the structured capabilities of a model.
        """
        model = self.get_model(model_id)
        if not model:
            return None
        capabilities_data = model.get("capabilities", {})
        return ModelCapabilities(capabilities_data)

    def build_runtime_package(self, model_id: str) -> ModelRuntimePackage | None:
        """
        Build and resolve the ModelRuntimePackage for a given model ID.
        Locates the model path, loads capabilities, and resolves component paths/runtimes.
        Supports the new Snapdragon Model Package Architecture (package.json)
        and falls back to legacy path resolution for backward compatibility.
        """
        model = self.get_model(model_id)
        if not model:
            print(f"[ModelRepository] Error: Model {model_id} not found.")
            return None

        model_path = model.get("path") or ""
        base_dir = Path(model_path) if model_path else Path("")
        
        # Check for package.json in the model directory (Snapdragon Model Package format)
        package_json_path = base_dir / "package.json" if model_path else Path("")
        
        from engine.model_runtime_package import ModelRuntimePackage
        
        if package_json_path.exists() and package_json_path.is_file():
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    package_data = json.load(f)
                
                if model_id not in ModelRepository._logged_smp_models:
                    print(f"[ModelRepository] Detected new Snapdragon Model Package format for '{model_id}'.")
                    ModelRepository._logged_smp_models.add(model_id)
                
                # Extract metadata
                pkg_ver = package_data.get("package_version", "1.0.0")
                author = package_data.get("author", model.get("author", ""))
                display_name = package_data.get("display_name", model.get("display_name", ""))
                
                # Extract capabilities
                capabilities = ModelCapabilities(package_data.get("capabilities", {}))
                
                # Extract components
                component_paths = {}
                component_runtimes = {}
                
                # Defined expected components for diffusion model pipeline
                expected_components = ["tokenizer", "tokenizer_2", "text_encoder", "text_encoder_2", "unet", "vae_decoder", "scheduler", "qnn_dlc"]
                components_config = package_data.get("components", {})
                
                for comp in expected_components:
                    comp_cfg = components_config.get(comp, {})
                    rel_path = comp_cfg.get("path", "")
                    
                    if rel_path:
                        # Resolve path relative to base_dir
                        component_paths[comp] = str((base_dir / rel_path).as_posix())
                    else:
                        component_paths[comp] = ""
                        
                    if not rel_path:
                        component_runtimes[comp] = ""
                    else:
                        if comp == "qnn_dlc":
                            default_runtime = "QNN_DLC"
                        elif comp in ["tokenizer", "tokenizer_2", "scheduler"]:
                            default_runtime = "CPU"
                        else:
                            default_runtime = "ONNX"
                        component_runtimes[comp] = comp_cfg.get("runtime", default_runtime)
                    
                return ModelRuntimePackage(
                    model_id=model_id,
                    base_path=base_dir,
                    capabilities=capabilities,
                    component_paths=component_paths,
                    component_runtimes=component_runtimes,
                    package_version=pkg_ver,
                    author=author,
                    display_name=display_name
                )
            except Exception as e:
                print(f"[ModelRepository] Error reading package.json for '{model_id}', falling back to legacy: {e}")
                
        # Legacy/Fallback path resolution (for backward compatibility)
        capabilities = self.get_model_capabilities(model_id)
        if not capabilities:
            capabilities = ModelCapabilities()
            
        # Define legacy component folders under base path
        component_paths = {
            "tokenizer": str((base_dir / "tokenizer").as_posix()) if model_path else "",
            "tokenizer_2": str((base_dir / "tokenizer_2").as_posix()) if model_path else "",
            "text_encoder": str((base_dir / "text_encoder" / "model.onnx").as_posix()) if model_path else "",
            "text_encoder_2": str((base_dir / "text_encoder_2" / "model.onnx").as_posix()) if model_path else "",
            "unet": str((base_dir / "unet" / "model.onnx").as_posix()) if model_path else "",
            "vae_decoder": str((base_dir / "vae_decoder" / "model.onnx").as_posix()) if model_path else "",
            "scheduler": str((base_dir / "scheduler").as_posix()) if model_path else "",
            "qnn_dlc": str((base_dir / "qnn_dlc" / "model.dlc").as_posix()) if model_path else ""
        }
        
        # Resolve runtime types based on model config
        backend_type = model.get("backend", "ONNX Runtime")
        if "DLC" in backend_type or "HTP" in backend_type:
            runtime_type = "QNN_DLC"
        elif "ONNX" in backend_type:
            runtime_type = "ONNX"
        else:
            runtime_type = "QNN"
        
        component_runtimes = {
            "tokenizer": "CPU",
            "tokenizer_2": "CPU",
            "text_encoder": runtime_type,
            "text_encoder_2": runtime_type,
            "unet": runtime_type,
            "vae_decoder": runtime_type,
            "scheduler": "CPU",
            "qnn_dlc": "QNN_DLC"
        }
        
        return ModelRuntimePackage(
            model_id=model_id,
            base_path=base_dir,
            capabilities=capabilities,
            component_paths=component_paths,
            component_runtimes=component_runtimes,
            package_version="1.0.0",
            author=model.get("author", ""),
            display_name=model.get("display_name", "")
        )

    def get_package_status(self, model_id: str) -> PackageStatus:
        """
        Determine the detailed PackageStatus of a model.
        """
        from controllers.package_status import PackageStatus
        model = self.get_model(model_id)
        if not model:
            return PackageStatus.NOT_INSTALLED
            
        installed = model.get("installed", False)
        if not installed:
            return PackageStatus.NOT_INSTALLED
            
        model_path = model.get("path") or ""
        if not model_path:
            return PackageStatus.NOT_INSTALLED
            
        base_dir = Path(model_path)
        if not base_dir.exists():
            return PackageStatus.NOT_INSTALLED
            
        package_json_path = base_dir / "package.json"
        if not package_json_path.exists():
            # Legacy package installed on disk
            return PackageStatus.INSTALLED
            
        # SMP package layout exists. Validate it.
        try:
            pkg = self.build_runtime_package(model_id)
            if not pkg:
                return PackageStatus.INVALID
                
            # Compare version for UPDATE_AVAILABLE
            repo_version = model.get("version", "1.0.0")
            pkg_version = pkg.package_version
            
            # Simple version comparison: if package version is less than repository version
            if repo_version != pkg_version and pkg_version < repo_version:
                return PackageStatus.UPDATE_AVAILABLE
                
            if pkg.is_fully_ready():
                return PackageStatus.READY
            elif pkg.is_valid_package():
                return PackageStatus.INSTALLED
            else:
                return PackageStatus.INVALID
        except Exception:
            return PackageStatus.INVALID







