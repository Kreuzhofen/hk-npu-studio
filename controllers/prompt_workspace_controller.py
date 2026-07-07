from __future__ import annotations

from controllers.prompt_workspace_model import PromptWorkspaceModel, PromptWorkspaceState
from controllers.generation_controller import GenerationController


class PromptWorkspaceController:
    """
    Controller for AI Image Generation Workspace.
    Acts as a mediator between UI state and the central GenerationController.
    """

    AVAILABLE_MODELS = [
        "sd_xl_base_1.0",
        "sd_xl_refiner_1.0",
        "sd_1.5_resnet",
        "flux_dev_quantized",
    ]

    def __init__(
        self,
        model: PromptWorkspaceModel | None = None,
        generation_controller: GenerationController | None = None,
    ) -> None:
        self.model = model or PromptWorkspaceModel()
        self.generation_controller = generation_controller or GenerationController()

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
        )

    def generate_image(self) -> None:
        # Delegate to GenerationController and update status
        status_msg = self.generation_controller.queue_generation()
        self.model.update_state(status=status_msg)
