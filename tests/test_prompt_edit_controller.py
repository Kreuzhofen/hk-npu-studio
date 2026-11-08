"""
Unit tests for Phoenix Prompt Engine Controller:
PromptEditController – Structured Edit Intent Routing, Safety Gates, and Background Protection

Created by Senior Software Engineer (Antigravity / Gemini)
Chief Software Architect: ChatGPT
Product Owner: Holger Kreuzhofen
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
from PIL import Image

from controllers.image_to_image_controller import ImageToImageController
from controllers.inpainting_controller import InpaintingController
from controllers.prompt_edit_controller import (
    PromptEditController,
    PromptEditPlan,
    PromptEditResult,
)
from engine.backends.sd15_qnn_inpainting_adapter import SD15QnnInpaintingResult
from engine.color_spatial_segmenter import ColorSpatialSegmenter, SegmentResult
from engine.prompt_intent_parser import IntentCategory, ParsedIntent, PromptIntentParser


class TestPromptEditController(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_prompt_ctrl_"))
        self.test_img_path = self.temp_dir / "test_input.png"
        self.test_out_path = self.temp_dir / "test_output.png"

        # Create a synthetic 512x512 test image with a red circle in the center
        img = Image.new("RGB", (512, 512), color=(200, 200, 200))
        # Draw red circle in center (radius 80)
        arr = np.array(img)
        y, x = np.ogrid[:512, :512]
        dist_from_center = (x - 256) ** 2 + (y - 256) ** 2
        red_mask = dist_from_center <= (80 ** 2)
        arr[red_mask] = [220, 30, 30]
        self.source_image = Image.fromarray(arr)
        self.source_image.save(self.test_img_path)

        # Mocks for backend controllers
        self.mock_inpainting = MagicMock(spec=InpaintingController)
        self.mock_inpainting.running = False
        self.mock_img2img = MagicMock(spec=ImageToImageController)
        self.mock_img2img.running = False

        self.controller = PromptEditController(
            inpainting_controller=self.mock_inpainting,
            img2img_controller=self.mock_img2img,
            parser=PromptIntentParser(),
            segmenter=ColorSpatialSegmenter(),
        )

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # 1. Initialization
    def test_controller_initialization(self):
        ctrl = PromptEditController()
        self.assertIsNotNone(ctrl.inpainting_controller)
        self.assertIsNotNone(ctrl.img2img_controller)
        self.assertIsNotNone(ctrl.parser)
        self.assertIsNotNone(ctrl.segmenter)
        self.assertFalse(ctrl.running)

    # 2. Safety Gate 1: Empty Prompt Rejection
    def test_analyze_empty_prompt_rejected(self):
        plan = self.controller.analyze(self.source_image, "   ")
        self.assertFalse(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.UNKNOWN)
        self.assertEqual(plan.controller_route, "NONE")
        self.assertIn("UNKNOWN", plan.rejection_reason or "")

    # 3. Safety Gate 1: Conversational / Non-editing Prompt Rejection
    def test_analyze_conversational_prompt_rejected(self):
        plan = self.controller.analyze(self.source_image, "Hallo, wer bist du und was kannst du?")
        self.assertFalse(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.UNKNOWN)
        self.assertEqual(plan.controller_route, "NONE")

    # 4. Safety Gate 1: Pure Description Rejection
    def test_analyze_pure_description_rejected(self):
        plan = self.controller.analyze(self.source_image, "Ein Foto von einem Hund auf der Wiese")
        self.assertFalse(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.UNKNOWN)

    # 5. Routing: Global Atmosphere Plan
    def test_analyze_global_atmosphere_routing(self):
        plan = self.controller.analyze(self.source_image, "Mache aus dem Tag einen Sonnenuntergang.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.GLOBAL_ATMOSPHERE)
        self.assertEqual(plan.mode, "GLOBAL")
        self.assertEqual(plan.controller_route, "IMG2IMG_GLOBAL")
        self.assertIsNone(plan.segment_result)
        self.assertIn("Sonnenuntergang", plan.refined_prompt)

    # 6. Routing: Material Transform 24k Gold
    def test_analyze_material_gold(self):
        plan = self.controller.analyze(self.source_image, "Verwandle den roten Apfel in 24k Gold.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(plan.mode, "LOCAL")
        self.assertEqual(plan.material_preset, "24k_gold")
        self.assertEqual(plan.controller_route, "INPAINTING_MATERIAL")
        self.assertIsNotNone(plan.segment_result)
        self.assertTrue(plan.segment_result.is_valid)

    # 7. Routing: Material Transform Antique Brass
    def test_analyze_material_brass(self):
        plan = self.controller.analyze(self.source_image, "Ändere den roten Gegenstand in Antik-Messing.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(plan.material_preset, "antique_brass")
        self.assertEqual(plan.controller_route, "INPAINTING_MATERIAL")

    # 8. Routing: Material Transform Copper
    def test_analyze_material_copper(self):
        plan = self.controller.analyze(self.source_image, "Verwandle das rote Objekt in Kupfer.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(plan.material_preset, "copper")
        self.assertEqual(plan.controller_route, "INPAINTING_MATERIAL")

    # 9. Routing: Material Transform Chrome
    def test_analyze_material_chrome(self):
        plan = self.controller.analyze(self.source_image, "Wandle den roten Kreis in Chrom um.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(plan.material_preset, "chrome")
        self.assertEqual(plan.controller_route, "INPAINTING_MATERIAL")

    # 10. Routing: Custom Leather Material
    def test_analyze_material_leather(self):
        plan = self.controller.analyze(self.source_image, "Ändere die rote Jacke in eine schwarze Lederjacke.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(plan.controller_route, "INPAINTING_MATERIAL")
        self.assertIn("leather", plan.refined_prompt.lower())

    # 11. Routing: Color Transform
    def test_analyze_color_transform(self):
        plan = self.controller.analyze(self.source_image, "Färbe das rote Objekt in blau.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.COLOR_TRANSFORM)
        self.assertEqual(plan.controller_route, "INPAINTING_COLOR")
        self.assertIn("blue", plan.refined_prompt.lower())

    # 12. Routing: Object Removal
    def test_analyze_object_removal(self):
        plan = self.controller.analyze(self.source_image, "Entferne das rote Objekt in der Mitte.")
        self.assertTrue(plan.can_execute)
        self.assertEqual(plan.intent, IntentCategory.OBJECT_REMOVAL)
        self.assertEqual(plan.controller_route, "INPAINTING_REMOVAL")
        self.assertEqual(plan.denoising_strength, 1.0)
        self.assertIn("Clean empty seamless background", plan.refined_prompt)

    # 13. Safety Gate 2: Non-existent Color Rejection
    def test_safety_gate_color_not_found(self):
        # Searching for cyan/blue in a neutral-gray + red image should fail segmentation
        plan = self.controller.analyze(self.source_image, "Verwandle das blaue Auto in Gold.")
        self.assertFalse(plan.can_execute)
        self.assertEqual(plan.controller_route, "NONE")
        self.assertIn("Sicherheitsabbruch Maskierung", plan.rejection_reason or "")

    # 14. Non-destructive safety check: Overwriting original is forbidden
    def test_execute_rejects_overwriting_original(self):
        with self.assertRaises(ValueError):
            self.controller.execute(
                input_image_path=self.test_img_path,
                prompt="Verwandle den roten Apfel in 24k Gold.",
                output_path=self.test_img_path,
            )

    # 15. File existence validation
    def test_execute_rejects_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            self.controller.execute(
                input_image_path=self.temp_dir / "non_existent.png",
                prompt="Verwandle den roten Apfel in 24k Gold.",
                output_path=self.test_out_path,
            )

    # 16. Execution Safety Gate Rejection (UNKNOWN prompt never calls NPU backend)
    def test_execute_aborts_on_unknown_prompt(self):
        result = self.controller.execute(
            input_image_path=self.test_img_path,
            prompt="Kannst du mir einen Witz erzählen?",
            output_path=self.test_out_path,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, "ERR_SAFETY_GATE_REJECTED")
        self.mock_inpainting._run_product_path.assert_not_called()
        self.mock_img2img._run_product_path.assert_not_called()

    # 17. Execution Routing: Material Transform calls Inpainting Controller
    def test_execute_material_transform_calls_inpainting(self):
        # Configure mock return
        dummy_result = SD15QnnInpaintingResult(
            success=True,
            output_path=self.test_out_path,
            metadata={"test": True},
        )
        self.mock_inpainting._run_product_path.return_value = dummy_result

        # Pre-create test output file so controller can open it
        self.source_image.save(self.test_out_path)

        result = self.controller.execute(
            input_image_path=self.test_img_path,
            prompt="Verwandle den roten Apfel in 24k Gold.",
            output_path=self.test_out_path,
        )
        self.assertTrue(result.success)
        self.mock_inpainting._run_product_path.assert_called_once()
        call_kwargs = self.mock_inpainting._run_product_path.call_args[1]
        self.assertEqual(call_kwargs["output_path"], self.test_out_path)
        self.assertIn("Gold", call_kwargs["prompt"])

    # 18. Execution Routing: Global Atmosphere calls ImageToImage Controller
    def test_execute_global_atmosphere_calls_img2img(self):
        dummy_result = SD15QnnInpaintingResult(
            success=True,
            output_path=self.test_out_path,
            metadata={"test": True},
        )
        self.mock_img2img._run_product_path.return_value = dummy_result
        self.source_image.save(self.test_out_path)

        result = self.controller.execute(
            input_image_path=self.test_img_path,
            prompt="Mache aus dem Tag einen Sonnenuntergang.",
            output_path=self.test_out_path,
        )
        self.assertTrue(result.success)
        self.mock_img2img._run_product_path.assert_called_once()
        call_kwargs = self.mock_img2img._run_product_path.call_args[1]
        self.assertTrue(call_kwargs["enable_reference_control"])
        self.assertEqual(call_kwargs["reference_mode"], "canny_qnn")

    # 19. Bit-exact Background Preservation Outside Mask
    def test_bit_exact_background_preservation(self):
        # Create a result image where background is accidentally altered
        res_arr = np.array(self.source_image).copy()
        # Alter a background pixel outside the red circle (e.g. at (10, 10))
        res_arr[10, 10] = [123, 234, 56]
        tampered_result = Image.fromarray(res_arr)

        mask = Image.new("L", (512, 512), 0)
        # Mask only covers center circle
        m_arr = np.array(mask)
        y, x = np.ogrid[:512, :512]
        m_arr[(x - 256) ** 2 + (y - 256) ** 2 <= (80 ** 2)] = 255
        mask = Image.fromarray(m_arr)

        out_file = self.temp_dir / "corrected.png"
        tampered_result.save(out_file)

        # Apply enforcement
        PromptEditController._verify_and_enforce_background_identity(
            source=self.source_image,
            result=tampered_result,
            mask=mask,
            out_path=out_file,
        )

        with Image.open(out_file) as reloaded:
            fixed_arr = np.array(reloaded)

        src_arr = np.array(self.source_image)
        # Pixels where mask == 0 must be 100% bit-identical
        untouched = (m_arr == 0)
        self.assertTrue(np.array_equal(fixed_arr[untouched], src_arr[untouched]))
        self.assertEqual(list(fixed_arr[10, 10]), list(src_arr[10, 10]))

    # 20. Sidecar JSON Metadata Generation
    def test_sidecar_metadata_generation(self):
        dummy_result = SD15QnnInpaintingResult(
            success=True,
            output_path=self.test_out_path,
            metadata={"model": "sd15_qnn"},
        )
        self.mock_inpainting._run_product_path.return_value = dummy_result
        self.source_image.save(self.test_out_path)

        result = self.controller.execute(
            input_image_path=self.test_img_path,
            prompt="Verwandle den roten Apfel in 24k Gold.",
            output_path=self.test_out_path,
        )
        self.assertTrue(result.success)

        sidecar_file = self.test_out_path.with_suffix(".json")
        self.assertTrue(sidecar_file.exists())

        with open(sidecar_file, encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["sprint"], "SPRINT_73")
        self.assertEqual(data["plan"]["material_preset"], "24k_gold")
        self.assertEqual(data["execution_evidence"]["cpu_fallback_count"], 0)
        self.assertEqual(data["execution_evidence"]["hardware"], "Qualcomm Hexagon NPU (HTP)")

    # 21. Cancellation Propagation
    def test_cancel_propagation(self):
        self.controller.cancel()
        self.mock_inpainting.cancel.assert_called_once()
        self.mock_img2img.cancel.assert_called_once()

    # 22. Asynchronous start() with callbacks
    def test_async_start_execution(self):
        dummy_result = SD15QnnInpaintingResult(
            success=True,
            output_path=self.test_out_path,
            metadata={"async": True},
        )
        self.mock_inpainting._run_product_path.return_value = dummy_result
        self.source_image.save(self.test_out_path)

        completed_events = []
        progress_events = []

        def on_prog(phase, val, msg):
            progress_events.append((phase, val))

        def on_done(res):
            completed_events.append(res)

        self.controller.start(
            input_image_path=self.test_img_path,
            prompt="Verwandle den roten Apfel in 24k Gold.",
            output_path=self.test_out_path,
            on_progress=on_prog,
            on_complete=on_done,
            asynchronous=False,  # Run synchronously to check in-thread
        )

        self.assertEqual(len(completed_events), 1)
        self.assertTrue(completed_events[0].success)
        self.assertGreater(len(progress_events), 0)


if __name__ == "__main__":
    unittest.main()
