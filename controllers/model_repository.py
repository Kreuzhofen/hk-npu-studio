from __future__ import annotations

import os
import json
from typing import Any


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

    @classmethod
    def get_active_model_id(cls) -> str | None:
        return cls._active_model_id

    @classmethod
    def set_active_model_id(cls, model_id: str | None) -> None:
        cls._active_model_id = model_id

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

        for filename in os.listdir(self.models_dir):
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

        if ModelRepository._active_model_id is None and self._models:
            ModelRepository._active_model_id = list(self._models.keys())[0]

    def _validate_model_data(self, data: dict[str, Any]) -> bool:
        """
        Validate required schema fields.
        """
        required_fields = {
            "id", "display_name", "author", "version", "license",
            "description", "category", "backend", "recommended_backend",
            "minimum_ram_gb", "recommended_ram_gb", "supports",
            "installed", "downloaded", "path", "status"
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
