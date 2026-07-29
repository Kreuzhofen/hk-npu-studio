from __future__ import annotations

from pathlib import Path

from controllers.generation_result import GenerationResult
from controllers.prompt_workspace_controller import PromptWorkspaceController
from controllers.prompt_workspace_model import PromptWorkspaceModel


class Repository:
    def get_product_models(self):
        return []

    def get_active_model_id(self):
        return None


class GenerationController:
    def __init__(self, results):
        self.repository = Repository()
        self.results = iter(results)

    def queue_generation(self, **kwargs):
        return next(self.results)

    def update_session(self, **kwargs):
        pass


def result(success, status, message, image_path=None):
    return GenerationResult(
        success=success,
        status=status,
        message=message,
        image_path=image_path,
        model_name="model",
    )


def test_failed_retry_preserves_last_successful_output(tmp_path, monkeypatch):
    image = tmp_path / "first.png"
    image.write_bytes(b"image")
    success = result(True, "FINISHED", "done", str(image))
    failure = result(False, "FAILED", "backend failed")
    generation = GenerationController([success, failure])
    controller = PromptWorkspaceController(
        model=PromptWorkspaceModel(),
        generation_controller=generation,
        repository=generation.repository,
    )
    monkeypatch.setattr(controller, "save_prompt_to_history", lambda prompt: None)

    assert controller.generate_image() is success
    assert controller.generate_image() is failure

    assert controller.last_response is success
    assert controller.last_attempt_response is failure
    assert controller.get_state().status == "error: backend failed"


def test_cancelled_retry_preserves_last_successful_output(tmp_path, monkeypatch):
    image = tmp_path / "first.png"
    image.write_bytes(b"image")
    success = result(True, "FINISHED", "done", str(image))
    cancelled = result(False, "CANCELLED", "cancelled")
    generation = GenerationController([success, cancelled])
    controller = PromptWorkspaceController(
        generation_controller=generation,
        repository=generation.repository,
    )
    monkeypatch.setattr(controller, "save_prompt_to_history", lambda prompt: None)

    controller.generate_image()
    controller.generate_image()

    assert controller.last_response is success
    assert controller.last_attempt_response is cancelled
    assert controller.get_state().status == "cancelled"


def test_successful_retry_replaces_previous_preview_output(tmp_path, monkeypatch):
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    first_path.write_bytes(b"first")
    second_path.write_bytes(b"second")
    first = result(True, "FINISHED", "done", str(first_path))
    second = result(True, "FINISHED", "done", str(second_path))
    generation = GenerationController([first, second])
    controller = PromptWorkspaceController(
        generation_controller=generation,
        repository=generation.repository,
    )
    monkeypatch.setattr(controller, "save_prompt_to_history", lambda prompt: None)

    controller.generate_image()
    controller.generate_image()

    assert controller.last_response is second
    assert Path(controller.last_response.image_path) == second_path


def test_missing_success_output_does_not_replace_previous_preview(tmp_path, monkeypatch):
    first_path = tmp_path / "first.png"
    first_path.write_bytes(b"first")
    first = result(True, "FINISHED", "done", str(first_path))
    missing = result(True, "FINISHED", "done", str(tmp_path / "missing.png"))
    generation = GenerationController([first, missing])
    controller = PromptWorkspaceController(
        generation_controller=generation,
        repository=generation.repository,
    )
    monkeypatch.setattr(controller, "save_prompt_to_history", lambda prompt: None)

    controller.generate_image()
    controller.generate_image()

    assert controller.last_response is first
    assert controller.last_attempt_response is missing
