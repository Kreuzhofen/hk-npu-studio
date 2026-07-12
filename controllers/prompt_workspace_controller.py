from __future__ import annotations

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
        )

    def generate_image(self, notify_workflow: bool = True) -> GenerationResult:
        # Delegate to GenerationController and update status.
        self.model.update_state(status="Generierung läuft")
        result = self.generation_controller.queue_generation(notify_workflow=notify_workflow)
        status_msg = "Abgeschlossen" if result.success else f"Fehler: {result.message}"
        self.model.update_state(status=status_msg)
        self.last_response = result
        return result
