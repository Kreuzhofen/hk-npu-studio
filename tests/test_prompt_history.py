from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from controllers.prompt_workspace_controller import PromptWorkspaceController
from controllers.prompt_workspace_model import PromptWorkspaceModel
from controllers.generation_controller import GenerationController
from controllers.model_repository import ModelRepository
from controllers.generation_result import GenerationResult
import config


class PromptHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_history_path = config.PROMPT_HISTORY_PATH
        config.PROMPT_HISTORY_PATH = Path(self.temp_dir.name) / "prompt_history.json"

        # Stub dependencies
        self.model = PromptWorkspaceModel()
        self.controller = PromptWorkspaceController(model=self.model)

    def tearDown(self) -> None:
        config.PROMPT_HISTORY_PATH = self.original_history_path
        self.temp_dir.cleanup()

    def test_load_empty_history(self) -> None:
        history = self.controller.load_prompt_history()
        self.assertEqual(history, [])

    def test_save_prompt_to_history(self) -> None:
        self.controller.save_prompt_to_history("A cybernetic cat")
        history = self.controller.load_prompt_history()
        self.assertEqual(history, ["A cybernetic cat"])

    def test_no_duplicates_newest_wins(self) -> None:
        self.controller.save_prompt_to_history("Prompt A")
        self.controller.save_prompt_to_history("Prompt B")
        self.controller.save_prompt_to_history("Prompt A")

        history = self.controller.load_prompt_history()
        self.assertEqual(history, ["Prompt A", "Prompt B"])

    def test_limit_to_20_entries(self) -> None:
        for i in range(25):
            self.controller.save_prompt_to_history(f"Prompt {i}")

        history = self.controller.load_prompt_history()
        self.assertEqual(len(history), 20)
        # The latest prompt (24) should be at index 0, and prompt 5 should be the oldest (index 19)
        self.assertEqual(history[0], "Prompt 24")
        self.assertEqual(history[-1], "Prompt 5")

    def test_persistence_between_controller_instances(self) -> None:
        self.controller.save_prompt_to_history("Persistent prompt")

        # Create a new controller instance using the same temp history path
        new_controller = PromptWorkspaceController()
        history = new_controller.load_prompt_history()
        self.assertEqual(history, ["Persistent prompt"])

    def test_only_successful_generations_saved(self) -> None:
        # Mock GenerationController.queue_generation to return success=False
        class MockGenCtrl:
            def queue_generation(self, notify_workflow=False):
                return GenerationResult(success=False, status="FAILED", message="Error")

        self.controller.generation_controller = MockGenCtrl()
        self.model.update_state(prompt="Failed prompt")
        self.controller.generate_image(notify_workflow=False)

        history = self.controller.load_prompt_history()
        self.assertNotIn("Failed prompt", history)

        # Mock queue_generation to return success=True
        class MockGenCtrlSuccess:
            def queue_generation(self, notify_workflow=False):
                return GenerationResult(success=True, status="SUCCESS", message="Done")

        self.controller.generation_controller = MockGenCtrlSuccess()
        self.model.update_state(prompt="Successful prompt")
        self.controller.generate_image(notify_workflow=False)

        history = self.controller.load_prompt_history()
        self.assertIn("Successful prompt", history)


if __name__ == "__main__":
    unittest.main()
