from __future__ import annotations

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock

from controllers.generation_session import GenerationSessionModel
from controllers.generation_job import GenerationJob
from controllers.generation_result import GenerationResult
from controllers.generation_pipeline import ImageGenerationPipeline
from controllers.prompt_workspace_controller import PromptWorkspaceController
import config


class SidecarMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original prompt history path
        self.original_history_path = config.PROMPT_HISTORY_PATH
        config.PROMPT_HISTORY_PATH = Path(self.temp_dir.name) / "prompt_history.json"

    def tearDown(self) -> None:
        config.PROMPT_HISTORY_PATH = self.original_history_path
        self.temp_dir.cleanup()

    def test_controlnet_generation_writes_sidecar(self) -> None:
        """1. Testet, dass eine ControlNet-Generierung ein JSON-Sidecar mit allen 6 ControlNet-Feldern schreibt."""
        image_path = self.output_dir / "generate_controlnet.png"
        
        # Create session with ControlNet settings
        session = GenerationSessionModel(
            model_name="controlnet_canny_qnn",
            input_image_path="C:\\SnapdragonAI\\input\\Typ.jpg",
            canny_low_threshold=60,
            canny_high_threshold=140,
            controlnet_conditioning_scale=1.5
        )
        
        job = GenerationJob(session=session)
        pipeline = ImageGenerationPipeline(job=job, backend_adapter=None)
        
        # Mock execute to return a dummy successful result
        pipeline.execute = MagicMock(return_value=GenerationResult(
            success=True,
            status="SUCCESS",
            message="Done",
            image_path=str(image_path)
        ))
        
        result = pipeline.run()
        self.assertTrue(result.success)
        
        # Verify JSON sidecar was created and contains the 6 fields
        sidecar_path = image_path.with_suffix(".json")
        self.assertTrue(sidecar_path.is_file())
        
        with open(sidecar_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertTrue(data.get("controlnet_enabled"))
        self.assertEqual(data.get("controlnet_model"), "canny")
        self.assertEqual(data.get("canny_low_threshold"), 60)
        self.assertEqual(data.get("canny_high_threshold"), 140)
        self.assertEqual(data.get("controlnet_conditioning_scale"), 1.5)
        self.assertEqual(data.get("reference_image_path"), "C:\\SnapdragonAI\\input\\Typ.jpg")

    def test_standard_generation_writes_sidecar_with_null_fields(self) -> None:
        """2. Testet, dass eine Standard-SD1.5-Generierung ein korrektes Sidecar ohne ungültige ControlNet-Werte erzeugt."""
        image_path = self.output_dir / "generate_standard.png"
        
        # Create session with standard SD1.5 settings
        session = GenerationSessionModel(
            model_name="sd_xl_base_1.0",
        )
        
        job = GenerationJob(session=session)
        pipeline = ImageGenerationPipeline(job=job, backend_adapter=None)
        
        # Mock execute to return a dummy successful result
        pipeline.execute = MagicMock(return_value=GenerationResult(
            success=True,
            status="SUCCESS",
            message="Done",
            image_path=str(image_path)
        ))
        
        result = pipeline.run()
        self.assertTrue(result.success)
        
        # Verify JSON sidecar was created and contains the fields set to null/false
        sidecar_path = image_path.with_suffix(".json")
        self.assertTrue(sidecar_path.is_file())
        
        with open(sidecar_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertFalse(data.get("controlnet_enabled"))
        self.assertIsNone(data.get("controlnet_model"))
        self.assertIsNone(data.get("canny_low_threshold"))
        self.assertIsNone(data.get("canny_high_threshold"))
        self.assertIsNone(data.get("controlnet_conditioning_scale"))
        self.assertIsNone(data.get("reference_image_path"))

    def test_load_old_history_entries_without_controlnet_keys(self) -> None:
        """3. Testet das Laden alter Historien-Einträge ohne ControlNet-Keys auf fehlerfreies Handling."""
        # Write an old history entry format (both strings and dicts missing controlnet keys)
        old_history = [
            "A beautiful vintage car",  # old string format
            {
                "prompt": "Cyberpunk city street",
                "model_name": "sd_xl_base_1.0",
                "width": 512,
                "height": 512,
                "steps": 20,
                "cfg_scale": 7.0,
                "seed": -1,
                "sampler": "Euler a",
                "scheduler": "Normal",
                # missing controlnet keys
            }
        ]
        
        with open(config.PROMPT_HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(old_history, f, indent=2, ensure_ascii=False)
            
        controller = PromptWorkspaceController()
        
        # 1. Load history as string list (default compatibility mode)
        history_strings = controller.load_prompt_history(return_dicts=False)
        self.assertEqual(len(history_strings), 2)
        self.assertEqual(history_strings[0], "A beautiful vintage car")
        self.assertEqual(history_strings[1], "Cyberpunk city street")
        
        # 2. Load history as dictionary list and verify fallback values are filled
        history_dicts = controller.load_prompt_history(return_dicts=True)
        self.assertEqual(len(history_dicts), 2)
        
        # Check first item (was string, converted to dict)
        self.assertEqual(history_dicts[0]["prompt"], "A beautiful vintage car")
        self.assertFalse(history_dicts[0]["controlnet_enabled"])
        self.assertIsNone(history_dicts[0]["controlnet_model"])
        self.assertIsNone(history_dicts[0]["canny_low_threshold"])
        
        # Check second item (was dict missing keys, now keys default to None/False)
        self.assertEqual(history_dicts[1]["prompt"], "Cyberpunk city street")
        self.assertFalse(history_dicts[1]["controlnet_enabled"])
        self.assertIsNone(history_dicts[1]["controlnet_model"])
        self.assertIsNone(history_dicts[1]["canny_low_threshold"])
