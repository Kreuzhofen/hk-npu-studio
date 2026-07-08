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
        self.generation_controller = generation_controller or GenerationController()
        self.repository = repository or ModelRepository()
        self.last_response: Any = None

        # Dynamically populate model names from the data-driven repository
        self.AVAILABLE_MODELS = [m["id"] for m in self.repository.get_all_models()]
        if not self.AVAILABLE_MODELS:
            self.AVAILABLE_MODELS = ["None"]

    def get_state(self) -> PromptWorkspaceState:
        return self.model.state

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

    def generate_image(self) -> GenerationResult:
        # Delegate to GenerationController and update status.
        self.model.update_state(status="Generierung läuft")
        result = self.generation_controller.queue_generation()
        status_msg = "Abgeschlossen" if result.success else f"Fehler: {result.message}"
        self.model.update_state(status=status_msg)
        self.last_response = result
        return result
