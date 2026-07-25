from __future__ import annotations

import json
import os
from typing import Any

from controllers.prompt_workspace_model import PromptWorkspaceModel, PromptWorkspaceState
from controllers.generation_controller import GenerationController
from controllers.model_repository import ModelRepository
from controllers.generation_result import GenerationResult


class PromptWorkspaceController:
    """
    Controller for AI Image Generation Workspace.
    Acts as a mediator between UI state, the central GenerationController, and ModelRepository.
    """

    def __init__(
        self,
        model: PromptWorkspaceModel | None = None,
        generation_controller: GenerationController | None = None,
        repository: ModelRepository | None = None,
    ) -> None:
        self.model = model or PromptWorkspaceModel()
        self.repository = repository or getattr(generation_controller, "repository", None) or ModelRepository()
        self.generation_controller = generation_controller or GenerationController(repository=self.repository)
        self.last_response: Any = None

        # Dynamically populate model names from the data-driven repository
        self.AVAILABLE_MODELS = [m["id"] for m in self.repository.get_product_models()]
        if not self.AVAILABLE_MODELS:
            self.AVAILABLE_MODELS = ["None"]

        active_model = self.repository.get_active_model_id()
        if active_model in self.AVAILABLE_MODELS:
            self.select_model(active_model)

    def get_state(self) -> PromptWorkspaceState:
        return self.model.state

    def get_generation_parameters(self, model_id: str) -> dict[str, Any] | None:
        """Return the central model-specific generation control contract."""
        return self.repository.get_generation_parameters(model_id)

    def select_model(self, model_id: str) -> dict[str, Any] | None:
        """Select a model and synchronize controller state to its metadata defaults."""
        contract = self.get_generation_parameters(model_id)
        if not contract:
            return None
        values = {
            name: spec.get("default")
            for name, spec in contract.items()
            if isinstance(spec, dict) and "default" in spec
        }
        self.repository.set_active_model_id(model_id)
        self.model.update_state(
            selected_model=model_id,
            width=values["width"], height=values["height"],
            steps=values["steps"], cfg=values["cfg"], seed=values["seed"],
            sampler=values["sampler"], scheduler=values["scheduler"],
        )
        self.generation_controller.update_session(
            model_name=model_id,
            width=values["width"], height=values["height"],
            steps=values["steps"], cfg_scale=values["cfg"], seed=values["seed"],
            sampler=values["sampler"], scheduler=values["scheduler"],
        )
        return contract

    def update_parameters(
        self,
        prompt: str,
        negative_prompt: str,
        seed: int,
        steps: int,
        cfg: float,
        width: int,
        height: int,
        selected_model: str,
        sampler: str = "Euler a",
        scheduler: str = "Normal",
        batch_size: int = 1,
        input_image_path: str | None = None,
        canny_low_threshold: int = 50,
        canny_high_threshold: int = 150,
        controlnet_conditioning_scale: float = 1.0,
    ) -> None:
        # Update local UI state model
        self.model.update_state(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            steps=steps,
            cfg=cfg,
            width=width,
            height=height,
            selected_model=selected_model,
            sampler=sampler,
            scheduler=scheduler,
            batch_count=batch_size,
            input_image_path=input_image_path,
            canny_low_threshold=canny_low_threshold,
            canny_high_threshold=canny_high_threshold,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
        )
        # Update central generation session parameters
        self.generation_controller.update_session(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            steps=steps,
            cfg_scale=cfg,
            width=width,
            height=height,
            model_name=selected_model,
            sampler=sampler,
            scheduler=scheduler,
            batch_size=batch_size,
            input_image_path=input_image_path,
            canny_low_threshold=canny_low_threshold,
            canny_high_threshold=canny_high_threshold,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
        )


    def generate_image(self, notify_workflow: bool = True) -> GenerationResult:
        # Delegate to GenerationController and update status.
        self.model.update_state(status="Generierung läuft")
        result = self.generation_controller.queue_generation(notify_workflow=notify_workflow)
        if result.status == "CANCELLED":
            status_msg = "CANCELLED"
        else:
            status_msg = "Abgeschlossen" if result.success else f"Fehler: {result.message}"
        self.model.update_state(status=status_msg)
        self.last_response = result
        if result.success and result.status != "CANCELLED":
            self.save_prompt_to_history(self.model.state.prompt)
        return result

    def load_prompt_history(self, return_dicts: bool = False) -> list[Any]:
        """Load prompt history from disk."""
        from config import PROMPT_HISTORY_PATH
        if not PROMPT_HISTORY_PATH.exists():
            return []
        try:
            with open(PROMPT_HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
            if isinstance(history, list):
                result = []
                for p in history:
                    if not p:
                        continue
                    if return_dicts:
                        # Normalize entries into dict if they are strings
                        if isinstance(p, str):
                            result.append({
                                "prompt": p,
                                "negative_prompt": "",
                                "model_name": "sd_xl_base_1.0",
                                "width": 512,
                                "height": 512,
                                "steps": 20,
                                "cfg_scale": 7.0,
                                "seed": -1,
                                "sampler": "Euler a",
                                "scheduler": "Normal",
                                "controlnet_enabled": False,
                                "controlnet_model": None,
                                "canny_low_threshold": None,
                                "canny_high_threshold": None,
                                "controlnet_conditioning_scale": None,
                                "reference_image_path": None,
                            })
                        else:
                            # Verify that controlnet keys are present in loaded dicts, fallback to None
                            # ensuring backward compatibility for entries missing these keys
                            entry = dict(p)
                            entry.setdefault("controlnet_enabled", False)
                            entry.setdefault("controlnet_model", None)
                            entry.setdefault("canny_low_threshold", None)
                            entry.setdefault("canny_high_threshold", None)
                            entry.setdefault("controlnet_conditioning_scale", None)
                            entry.setdefault("reference_image_path", None)
                            result.append(entry)
                    else:
                        if isinstance(p, dict):
                            result.append(p.get("prompt", ""))
                        else:
                            result.append(str(p))
                return result
        except Exception as e:
            print(f"[PromptWorkspaceController] Error loading prompt history: {e}")
        return []

    def save_prompt_to_history(self, prompt: str) -> None:
        """Add a prompt to history, ensuring uniqueness, ordering, and size limit of 20."""
        prompt = prompt.strip()
        if not prompt:
            return
        from config import PROMPT_HISTORY_PATH
        history = self.load_prompt_history(return_dicts=True)

        controlnet_enabled = False
        try:
            model_name = self.model.state.selected_model
            model_meta = self.generation_controller.repository.get_model(model_name)
            if model_meta:
                capabilities = model_meta.get("capabilities", {})
                controlnet_enabled = capabilities.get("controlnet", False)
        except Exception:
            pass

        entry = {
            "prompt": prompt,
            "negative_prompt": self.model.state.negative_prompt,
            "model_name": self.model.state.selected_model,
            "width": self.model.state.width,
            "height": self.model.state.height,
            "steps": self.model.state.steps,
            "cfg_scale": self.model.state.cfg,
            "seed": self.model.state.seed,
            "sampler": self.model.state.sampler,
            "scheduler": self.model.state.scheduler,
            "controlnet_enabled": controlnet_enabled,
            "controlnet_model": "canny" if controlnet_enabled else None,
            "canny_low_threshold": self.model.state.canny_low_threshold if controlnet_enabled else None,
            "canny_high_threshold": self.model.state.canny_high_threshold if controlnet_enabled else None,
            "controlnet_conditioning_scale": self.model.state.controlnet_conditioning_scale if controlnet_enabled else None,
            "reference_image_path": self.model.state.input_image_path if controlnet_enabled else None,
        }

        # Check duplicates based on prompt string (newest wins)
        new_history = []
        for h in history:
            h_prompt = h.get("prompt", "") if isinstance(h, dict) else str(h)
            if h_prompt.strip() != prompt:
                new_history.append(h)

        new_history.insert(0, entry)

        # Limit to 20 entries
        new_history = new_history[:20]

        try:
            PROMPT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            temp_path = PROMPT_HISTORY_PATH.with_suffix(PROMPT_HISTORY_PATH.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(new_history, f, indent=2, ensure_ascii=False)
            if os.path.exists(PROMPT_HISTORY_PATH):
                os.remove(PROMPT_HISTORY_PATH)
            os.rename(temp_path, PROMPT_HISTORY_PATH)
        except Exception as e:
            print(f"[PromptWorkspaceController] Error saving prompt history: {e}")

    def load_prompt_templates(self) -> dict[str, list[dict[str, str]]]:
        """Load prompt templates from resources JSON file."""
        from config import PROMPT_TEMPLATES_PATH
        if not PROMPT_TEMPLATES_PATH.exists():
            return {}
        try:
            with open(PROMPT_TEMPLATES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "categories" in data:
                return data["categories"]
        except Exception as e:
            print(f"[PromptWorkspaceController] Error loading prompt templates: {e}")
        return {}

    def cancel_generation(self) -> str:
        """Use the existing generation-controller cancellation path."""
        status = self.generation_controller.cancel_generation()
        self.model.update_state(status="CANCELLED")
        return status
