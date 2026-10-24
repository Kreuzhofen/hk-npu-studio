from __future__ import annotations

import json
import os
import time
from pathlib import Path
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
        self.last_attempt_response: Any = None

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
        controlnet_enabled: bool | None = None,
        canny_low_threshold: int = 50,
        canny_high_threshold: int = 150,
        controlnet_conditioning_scale: float = 1.0,
        phoenix_boost_enabled: bool = False,
        upscale_profile: str = "off",
    ) -> None:
        effective_controlnet_enabled = (
            self.model.state.controlnet_enabled
            if controlnet_enabled is None
            else bool(controlnet_enabled)
        )
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
            controlnet_enabled=effective_controlnet_enabled,
            canny_low_threshold=canny_low_threshold,
            canny_high_threshold=canny_high_threshold,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            phoenix_boost_enabled=bool(phoenix_boost_enabled),
            upscale_profile=str(upscale_profile),
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
            controlnet_enabled=effective_controlnet_enabled,
            canny_low_threshold=canny_low_threshold,
            canny_high_threshold=canny_high_threshold,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            phoenix_boost_enabled=bool(phoenix_boost_enabled),
        )

    def restore_generation_settings(self, settings: dict[str, Any]) -> None:
        """Synchronize controller model and generation session with restored persistent settings."""
        if not isinstance(settings, dict):
            return
        model_id = (
            settings.get("model_name")
            or settings.get("selected_model")
            or getattr(self.model.state, "selected_model", "sd_xl_base_1.0")
        )
        if model_id in self.AVAILABLE_MODELS and model_id != getattr(self.model.state, "selected_model", None):
            self.select_model(model_id)

        prompt = str(settings.get("prompt", getattr(self.model.state, "prompt", "")))
        neg_prompt = str(settings.get("negative_prompt", getattr(self.model.state, "negative_prompt", "")))
        try:
            seed = int(settings.get("seed", getattr(self.model.state, "seed", -1)))
        except (TypeError, ValueError):
            seed = -1
        try:
            steps = int(settings.get("steps", getattr(self.model.state, "steps", 20)))
        except (TypeError, ValueError):
            steps = 20
        try:
            cfg = float(settings.get("cfg_scale", settings.get("cfg", getattr(self.model.state, "cfg", 7.0))))
        except (TypeError, ValueError):
            cfg = 7.0
        try:
            width = int(settings.get("width", getattr(self.model.state, "width", 512)))
        except (TypeError, ValueError):
            width = 512
        try:
            height = int(settings.get("height", getattr(self.model.state, "height", 512)))
        except (TypeError, ValueError):
            height = 512
        sampler = str(settings.get("sampler", getattr(self.model.state, "sampler", "Euler a")))
        scheduler = str(settings.get("scheduler", getattr(self.model.state, "scheduler", "Normal")))
        try:
            batch_size = int(
                settings.get("batch_size", settings.get("batch_count", getattr(self.model.state, "batch_count", 1)))
            )
        except (TypeError, ValueError):
            batch_size = 1
        upscale_profile = str(settings.get("upscale_profile", getattr(self.model.state, "upscale_profile", "off")))
        controlnet_enabled = bool(
            settings.get("controlnet_enabled", getattr(self.model.state, "controlnet_enabled", False))
        )
        try:
            canny_low = int(settings.get("canny_low_threshold", getattr(self.model.state, "canny_low_threshold", 50)))
        except (TypeError, ValueError):
            canny_low = 50
        try:
            canny_high = int(settings.get("canny_high_threshold", getattr(self.model.state, "canny_high_threshold", 150)))
        except (TypeError, ValueError):
            canny_high = 150
        try:
            cond_scale = float(
                settings.get("controlnet_conditioning_scale", getattr(self.model.state, "controlnet_conditioning_scale", 1.0))
            )
        except (TypeError, ValueError):
            cond_scale = 1.0
        input_image = settings.get(
            "input_image_path",
            settings.get("reference_image_path", getattr(self.model.state, "input_image_path", None)),
        )
        boost_enabled = bool(
            settings.get("phoenix_boost_enabled", getattr(self.model.state, "phoenix_boost_enabled", False))
        )

        self.update_parameters(
            prompt=prompt,
            negative_prompt=neg_prompt,
            seed=seed,
            steps=steps,
            cfg=cfg,
            width=width,
            height=height,
            selected_model=model_id,
            sampler=sampler,
            scheduler=scheduler,
            batch_size=batch_size,
            input_image_path=input_image,
            controlnet_enabled=controlnet_enabled,
            canny_low_threshold=canny_low,
            canny_high_threshold=canny_high,
            controlnet_conditioning_scale=cond_scale,
            phoenix_boost_enabled=boost_enabled,
            upscale_profile=upscale_profile,
        )


    def generate_image(self, notify_workflow: bool = True, progress_callback: Any = None) -> GenerationResult:
        # Delegate to GenerationController and update status.
        self.model.update_state(status="generating")
        result = self.generation_controller.queue_generation(notify_workflow=notify_workflow, progress_callback=progress_callback)
        if result.status == "CANCELLED":
            status_msg = "cancelled"
        else:
            status_msg = "completed" if result.success else f"error: {result.message}"
        self.model.update_state(status=status_msg)
        self.last_attempt_response = result
        if (
            result.success
            and result.status != "CANCELLED"
            and result.image_path
            and Path(result.image_path).is_file()
        ):
            self.last_response = result
            self.save_prompt_to_history(self.model.state.prompt)
        return result

    def upscale_generated_image(self, image_path: str, scale: int) -> str:
        """Create a separate RealESRGAN-QNN result for the requested profile."""
        from PIL import Image
        from engine.file_utils import get_unique_filename
        from engine.phoenix_adapter import PhoenixAdapter

        if scale not in (2, 4):
            raise ValueError(f"Unsupported RealESRGAN scale: {scale}")

        source_path = Path(image_path).resolve()
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        upscale_result = PhoenixAdapter().run("image.upscale", input_path=str(source_path))
        intermediate_path = Path(str(upscale_result["output_path"])).resolve()
        if not intermediate_path.is_file():
            raise FileNotFoundError(intermediate_path)
        if intermediate_path == source_path:
            raise RuntimeError("RealESRGAN must return a separate output file")

        target_path = get_unique_filename(
            source_path.parent,
            f"{source_path.stem}_{scale}x.png",
        )
        if scale == 2:
            with Image.open(source_path) as original, Image.open(intermediate_path) as enhanced:
                target_size = (original.width * 2, original.height * 2)
                enhanced.resize(target_size, Image.Resampling.LANCZOS).save(target_path)
        elif intermediate_path != target_path.resolve():
            for attempt in range(5):
                try:
                    intermediate_path.replace(target_path)
                    break
                except OSError as error:
                    if getattr(error, "winerror", None) != 32 or attempt == 4:
                        raise
                    time.sleep(0.1 * (attempt + 1))

        if intermediate_path not in {source_path, target_path.resolve()}:
            intermediate_path.unlink(missing_ok=True)
        return str(target_path.resolve())

    def upscale_generated_image_2x(self, image_path: str) -> str:
        """Compatibility wrapper for callers using the former 2x-only API."""
        return self.upscale_generated_image(image_path, 2)

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

        controlnet_enabled = bool(self.model.state.controlnet_enabled)

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

    def clear_prompt_history(self) -> None:
        """Clear saved generation-history entries without touching generated files."""
        from config import PROMPT_HISTORY_PATH

        try:
            PROMPT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            temp_path = PROMPT_HISTORY_PATH.with_suffix(PROMPT_HISTORY_PATH.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            os.replace(temp_path, PROMPT_HISTORY_PATH)
        except Exception as e:
            print(f"[PromptWorkspaceController] Error clearing prompt history: {e}")

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
        self.model.update_state(status="cancelled")
        return status
