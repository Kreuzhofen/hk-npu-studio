from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk

from app.configuration_manager import (
    CURRENT_SCHEMA_VERSION,
    DEFAULT_GENERATION_SETTINGS,
    ConfigurationManager,
)
from app.settings_manager import SettingsManager
from controllers.prompt_workspace_controller import PromptWorkspaceController
from controllers.prompt_workspace_model import PromptWorkspaceModel, PromptWorkspaceState
from controllers.generation_session import GenerationSessionModel, PipelineParameters
from widgets.phoenix.views.prompt_view import PhoenixPromptView


class GenerationSettingsPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.root.destroy()
        except Exception:
            pass

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pref_path = Path(self.temp_dir.name) / "preferences.json"
        self.patcher = patch.object(
            SettingsManager, "get_preferences_path", return_value=self.pref_path
        )
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_default_generation_settings_when_file_missing(self) -> None:
        """Missing config should return safe, validated default settings."""
        self.assertFalse(self.pref_path.exists())
        settings = SettingsManager.get_generation_settings()

        self.assertIsInstance(settings, dict)
        self.assertEqual(settings["prompt"], "")
        self.assertEqual(settings["negative_prompt"], "")
        self.assertEqual(settings["seed"], -1)
        self.assertEqual(settings["steps"], 20)
        self.assertEqual(settings["cfg_scale"], 7.5)
        self.assertEqual(settings["width"], 512)
        self.assertEqual(settings["height"], 512)
        self.assertEqual(settings["sampler"], "Euler")
        self.assertEqual(settings["scheduler"], "Normal")
        self.assertEqual(settings["batch_size"], 1)
        self.assertEqual(settings["upscale_profile"], "off")
        self.assertFalse(settings["controlnet_enabled"])
        self.assertEqual(settings["canny_low_threshold"], 50)
        self.assertEqual(settings["canny_high_threshold"], 150)
        self.assertEqual(settings["controlnet_conditioning_scale"], 1.0)
        self.assertIsNone(settings["input_image_path"])
        self.assertFalse(settings["phoenix_boost_enabled"])

    def test_save_and_restore_all_parameters(self) -> None:
        """Saving generation settings persists all fields to disk and restores them."""
        payload = {
            "prompt": "A majestic phoenix rising above a cyberpunk metropolis",
            "negative_prompt": "blurry, low quality, artifacts, watermark",
            "model_name": "stable_diffusion_v3_5_qai",
            "seed": 987654,
            "steps": 28,
            "cfg_scale": 8.0,
            "width": 1024,
            "height": 1024,
            "sampler": "Euler a",
            "scheduler": "Normal",
            "batch_size": 2,
            "upscale_profile": "2",
            "controlnet_enabled": True,
            "canny_low_threshold": 65,
            "canny_high_threshold": 175,
            "controlnet_conditioning_scale": 0.85,
            "input_image_path": "C:\\images\\ref.png",
            "phoenix_boost_enabled": False,
        }

        saved = SettingsManager.save_generation_settings(payload)
        self.assertTrue(saved)
        self.assertTrue(self.pref_path.exists())

        restored = SettingsManager.get_generation_settings()
        for key, expected_value in payload.items():
            self.assertEqual(
                restored[key],
                expected_value,
                f"Field '{key}' mismatch: expected {expected_value}, got {restored.get(key)}",
            )

    def test_sync_with_legacy_and_active_model_keys(self) -> None:
        """Changes to generation settings synchronize with last_prompt and active_model_id."""
        SettingsManager.save_generation_settings({
            "prompt": "futuristic car in desert",
            "negative_prompt": "trees, water",
            "model_name": "stable_diffusion_v2_1_qnn",
        })

        raw = json.loads(self.pref_path.read_text(encoding="utf-8"))
        self.assertEqual(raw["last_prompt"], "futuristic car in desert")
        self.assertEqual(raw["last_negative_prompt"], "trees, water")
        self.assertEqual(raw["active_model_id"], "stable_diffusion_v2_1_qnn")

        # Also test legacy set_last_prompt updates generation_settings
        SettingsManager.set_last_prompt("updated prompt via legacy method")
        gen = SettingsManager.get_generation_settings()
        self.assertEqual(gen["prompt"], "updated prompt via legacy method")
        self.assertEqual(SettingsManager.get_last_prompt(), "updated prompt via legacy method")

    def test_migration_from_v1_and_v2_preserves_existing_user_data(self) -> None:
        """Older preferences schemas (v1, v2) migrate cleanly without losing user settings."""
        v2_data = {
            "schema_version": 2,
            "active_model_id": "custom_migrated_model",
            "hf_token": "hf_test_token_12345",
            "thread_count": "4",
            "execution_provider": "CPU EP",
            "hardware_accel": "False",
            "output_dir": "C:\\CustomOutput",
            "models_dir": "C:\\CustomModels",
            "theme": "Hell",
            "language": "English",
            "last_prompt": "portrait of an old captain",
            "last_negative_prompt": "ugly, bad anatomy",
        }
        self.pref_path.write_text(json.dumps(v2_data), encoding="utf-8")

        mgr = ConfigurationManager(self.pref_path)
        loaded = mgr.load()

        self.assertEqual(CURRENT_SCHEMA_VERSION, loaded["schema_version"])
        self.assertEqual("custom_migrated_model", loaded["active_model_id"])
        self.assertEqual("hf_test_token_12345", loaded["hf_token"])
        self.assertEqual("4", loaded["thread_count"])
        self.assertEqual("CPU EP", loaded["execution_provider"])
        self.assertEqual("False", loaded["hardware_accel"])
        self.assertEqual("C:\\CustomOutput", loaded["output_dir"])
        self.assertEqual("Hell", loaded["theme"])
        self.assertEqual("English", loaded["language"])

        # Check migrated generation_settings
        gen = loaded["generation_settings"]
        self.assertIsInstance(gen, dict)
        self.assertEqual(gen["prompt"], "portrait of an old captain")
        self.assertEqual(gen["negative_prompt"], "ugly, bad anatomy")
        self.assertEqual(gen["model_name"], "custom_migrated_model")
        self.assertEqual(gen["steps"], 20)
        self.assertEqual(gen["cfg_scale"], 7.5)

    def test_robust_validation_of_invalid_and_out_of_range_data(self) -> None:
        """Corrupted, out-of-range, or mistyped data falls back to safe defaults without crashing."""
        corrupted = {
            "generation_settings": {
                "prompt": 12345,  # should convert to string
                "negative_prompt": None,  # should convert to string
                "seed": "not-a-number",  # should fall back to -1
                "steps": -99,  # out of range, should fall back to 20
                "cfg_scale": "invalid",  # should fall back to 7.5
                "width": 99999,  # out of range, should fall back to 512
                "height": -512,  # out of range, should fall back to 512
                "sampler": "",  # empty, should fall back to Euler
                "batch_size": 999,  # out of range, should fall back to 1
                "upscale_profile": "ultra-max-64x",  # invalid, should fall back to "off"
                "canny_low_threshold": -50,  # out of range, should fall back to 50
                "controlnet_conditioning_scale": 15.0,  # out of range, should fall back to 1.0
            }
        }
        self.pref_path.write_text(json.dumps(corrupted), encoding="utf-8")

        mgr = ConfigurationManager(self.pref_path)
        loaded = mgr.load()
        gen = loaded["generation_settings"]

        self.assertEqual(gen["prompt"], "12345")
        self.assertEqual(gen["negative_prompt"], "")
        self.assertEqual(gen["seed"], -1)
        self.assertEqual(gen["steps"], 20)
        self.assertEqual(gen["cfg_scale"], 7.5)
        self.assertEqual(gen["width"], 512)
        self.assertEqual(gen["height"], 512)
        self.assertEqual(gen["sampler"], "Euler")
        self.assertEqual(gen["batch_size"], 1)
        self.assertEqual(gen["upscale_profile"], "off")
        self.assertEqual(gen["canny_low_threshold"], 50)
        self.assertEqual(gen["controlnet_conditioning_scale"], 1.0)

    def test_mvc_and_pipeline_consistency(self) -> None:
        """Verify UI, PromptWorkspaceModel, GenerationSessionModel, and PipelineParameters consistency."""
        controller_tmp = PromptWorkspaceController()
        available = controller_tmp.AVAILABLE_MODELS
        test_model = "stable_diffusion_v2_1_qnn" if "stable_diffusion_v2_1_qnn" in available else available[0]
        contract = controller_tmp.get_generation_parameters(test_model) or {}

        # Resolve valid contract values for the test model
        valid_width = contract.get("width", {}).get("default", 512) if isinstance(contract.get("width"), dict) else 512
        valid_height = contract.get("height", {}).get("default", 512) if isinstance(contract.get("height"), dict) else 512
        valid_sampler = contract.get("sampler", {}).get("default", "DDIM") if isinstance(contract.get("sampler"), dict) else "DDIM"
        valid_scheduler = contract.get("scheduler", {}).get("default", "DDIM") if isinstance(contract.get("scheduler"), dict) else "DDIM"

        SettingsManager.save_generation_settings({
            "prompt": "golden retriever in autumn leaves",
            "negative_prompt": "oversaturated",
            "model_name": test_model,
            "seed": 42,
            "steps": 25,
            "cfg_scale": 6.5,
            "width": valid_width,
            "height": valid_height,
            "sampler": valid_sampler,
            "scheduler": valid_scheduler,
            "batch_size": 1,
            "upscale_profile": "off",
        })

        controller = PromptWorkspaceController()
        view = PhoenixPromptView(self.root, controller=controller)
        try:
            # 1. UI variables match
            self.assertEqual(view.prompt_text.get("1.0", "end-1c").strip(), "golden retriever in autumn leaves")
            self.assertEqual(view.neg_prompt_text.get("1.0", "end-1c").strip(), "oversaturated")
            self.assertEqual(view.seed_var.get(), "42")
            self.assertEqual(int(view.steps_var.get()), 25)
            self.assertEqual(float(view.cfg_var.get()), 6.5)
            self.assertEqual(int(view.width_var.get()), valid_width)
            self.assertEqual(int(view.height_var.get()), valid_height)
            self.assertEqual(view.sampler_var.get(), valid_sampler)
            self.assertEqual(view.scheduler_var.get(), valid_scheduler)

            # 2. PromptWorkspaceModel matches
            state = controller.get_state()
            self.assertEqual(state.prompt, "golden retriever in autumn leaves")
            self.assertEqual(state.negative_prompt, "oversaturated")
            self.assertEqual(state.seed, 42)
            self.assertEqual(state.steps, 25)
            self.assertEqual(state.cfg, 6.5)
            self.assertEqual(state.width, valid_width)
            self.assertEqual(state.height, valid_height)
            self.assertEqual(state.sampler, valid_sampler)

            # 3. GenerationSessionModel matches
            session = controller.generation_controller.session
            self.assertEqual(session.prompt, "golden retriever in autumn leaves")
            self.assertEqual(session.steps, 25)
            self.assertEqual(session.cfg_scale, 6.5)
            self.assertEqual(session.width, valid_width)
            self.assertEqual(session.height, valid_height)

            # 4. PipelineParameters matches
            params = PipelineParameters.from_session(session)
            self.assertEqual(params.prompt, "golden retriever in autumn leaves")
            self.assertEqual(params.steps, 25)
            self.assertEqual(params.cfg_scale, 6.5)
            self.assertEqual(params.seed, 42)
            self.assertEqual(params.width, valid_width)
            self.assertEqual(params.height, valid_height)
        finally:
            view.destroy()
            self.root.update_idletasks()

    def test_simulated_restart_restores_user_state(self) -> None:
        """Simulate an application restart: user modifies settings, app closes, restarts and restores exact state."""
        # 1. First session
        controller1 = PromptWorkspaceController()
        view1 = PhoenixPromptView(self.root, controller=controller1)

        view1.prompt_text.delete("1.0", "end")
        view1.prompt_text.insert("1.0", "A cozy alpine wooden cabin in snow at dusk")
        view1.neg_prompt_text.delete("1.0", "end")
        view1.neg_prompt_text.insert("1.0", "blurry, dark, low quality")
        view1.steps_var.set(33)
        view1.cfg_var.set(8.5)
        view1.seed_var.set("777")
        view1.batch_var.set("2")
        view1._set_upscale_profile("2")

        # Save and close first session
        view1._sync_parameters_to_controller()
        view1._save_all_generation_settings_now()
        view1.destroy()
        self.root.update_idletasks()

        # 2. Restart session (new controller, new view)
        controller2 = PromptWorkspaceController()
        view2 = PhoenixPromptView(self.root, controller=controller2)
        try:
            # Verify restored UI values
            self.assertEqual(view2.prompt_text.get("1.0", "end-1c").strip(), "A cozy alpine wooden cabin in snow at dusk")
            self.assertEqual(view2.neg_prompt_text.get("1.0", "end-1c").strip(), "blurry, dark, low quality")
            self.assertEqual(int(view2.steps_var.get()), 33)
            self.assertEqual(float(view2.cfg_var.get()), 8.5)
            self.assertEqual(view2.seed_var.get(), "777")
            self.assertEqual(int(view2.batch_var.get()), 2)
            self.assertEqual(view2.upscale_profile_var.get(), "2")

            # Verify restored controller and session values
            state2 = controller2.get_state()
            self.assertEqual(state2.steps, 33)
            self.assertEqual(state2.cfg, 8.5)
            self.assertEqual(state2.seed, 777)
            self.assertEqual(state2.batch_count, 2)
            self.assertEqual(state2.upscale_profile, "2")
        finally:
            view2.destroy()
            self.root.update_idletasks()


if __name__ == "__main__":
    unittest.main()
