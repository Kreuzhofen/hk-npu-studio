from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any
from controllers.model_repository import ModelRepository
from controllers.generation_result import GenerationResult


@dataclass
class WorkflowState:
    """
    State representing shared parameters across various workspaces.
    Transient in-memory state.
    """
    active_model: str | None = None
    last_generated_image: str | None = None
    selected_gallery_image: str | None = None
    selected_compare_image: str | None = None


class WorkflowController:
    """
    Central mediator to coordinate views and navigation transitions across workspaces.
    Adheres to MVC by preventing direct View-to-View communication.
    """
    _instance: WorkflowController | None = None

    def __new__(cls, *args, **kwargs) -> WorkflowController:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, app: Any = None, workspace: Any = None) -> None:
        # Prevent re-initialization if already constructed
        if hasattr(self, "_initialized") and self._initialized:
            # Overwrite references if passed in later
            if app is not None:
                self.app = app
            if workspace is not None:
                self.workspace = workspace
            return
            
        self.app = app
        self.workspace = workspace
        self.state = WorkflowState()
        self._initialized = True

    @classmethod
    def get_instance(cls) -> WorkflowController:
        """Retrieve the global WorkflowController instance."""
        if cls._instance is None:
            cls._instance = WorkflowController()
        return cls._instance

    def open_generate(self) -> None:
        """Switch the workspace cleanly to the AI Generate view."""
        if self.workspace:
            self.workspace.show_view("prompt")

    def open_gallery(self) -> None:
        """Switch the workspace cleanly to the Gallery (AI Asset Library) view."""
        if self.workspace:
            self.workspace.show_view("gallery")

    def open_compare(self) -> None:
        """Switch the workspace cleanly to the Compare (Review Workspace) view."""
        if self.workspace:
            self.workspace.show_view("compare")

    def open_model_manager(self) -> None:
        """Switch the workspace cleanly to the AI Model Manager view."""
        if self.workspace:
            self.workspace.show_view("models")

    def get_state(self) -> WorkflowState:
        """Retrieve the current cross-workspace workflow state."""
        # Keep state synchronized with single source of truth active model
        self.state.active_model = ModelRepository.get_active_model_id()
        return self.state

    def on_generation_finished(self, result: GenerationResult) -> None:
        """Register successful generation outputs for Gallery and Review workspaces."""
        if result.success and result.image_path:
            self._append_generation_diagnostic(result, "before_workflow_state_update")
            self.state.last_generated_image = result.image_path
            self.state.selected_gallery_image = result.image_path
            self.state.selected_compare_image = result.image_path
            self._append_generation_diagnostic(result, "after_workflow_state_update")

            if self.workspace is not None:
                try:
                    self._append_generation_diagnostic(result, "before_gallery_refresh")
                    gallery_view = self.workspace._get_or_create_view("gallery")
                    show_generated = getattr(gallery_view, "show_generated_image", None)
                    if callable(show_generated):
                        show_generated(result.image_path)
                    self._append_generation_diagnostic(result, "after_gallery_refresh")
                except Exception as error:
                    self._append_generation_diagnostic(result, "gallery_refresh_exception", str(error))
                    print(f"[WorkflowController] Gallery update skipped: {error}")

        print(f"[WorkflowController] Generation Finished Callback. Success={result.success}, Status={result.status}")

    def _append_generation_diagnostic(self, result: GenerationResult, step: str, details: str = "") -> None:
        metadata = getattr(result, "metadata", None)
        if not isinstance(metadata, dict):
            return
        log_path = metadata.get("diagnostic_log_path")
        if not log_path:
            return
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        line = f"[{timestamp}] {step}"
        if details:
            line = f"{line} | {details}"
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(line + "\n")
        except Exception:
            pass
