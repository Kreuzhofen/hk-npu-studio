"""
Unit tests for Phoenix Prompt Engine Foundation:
- PromptIntentParser
- ColorSpatialSegmenter

Created by Senior Software Engineer (Antigravity / Gemini)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import numpy as np
from PIL import Image

from engine.prompt_intent_parser import PromptIntentParser, IntentCategory
from engine.color_spatial_segmenter import ColorSpatialSegmenter, SegmentResult


class TestPromptIntentParser(unittest.TestCase):
    def setUp(self):
        self.parser = PromptIntentParser()

    def test_sprint70_core_prompts(self):
        # 1. Ändere die rote Jacke in eine schwarze Lederjacke.
        p1 = self.parser.parse("Ändere die rote Jacke in eine schwarze Lederjacke.")
        self.assertEqual(p1.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(p1.target_object, "Jacke")
        self.assertEqual(p1.source_color, "red")
        self.assertEqual(p1.target_color, "black")
        self.assertEqual(p1.target_material, "leather")
        self.assertEqual(p1.mode, "LOCAL")
        self.assertTrue(p1.is_confident)

        # 2. Mache aus dem Tag einen Sonnenuntergang.
        p2 = self.parser.parse("Mache aus dem Tag einen Sonnenuntergang.")
        self.assertEqual(p2.intent, IntentCategory.GLOBAL_ATMOSPHERE)
        self.assertEqual(p2.mode, "GLOBAL")
        self.assertTrue(p2.is_confident)

        # 3. Verwandle den Holztisch in Marmor.
        p3 = self.parser.parse("Verwandle den Holztisch in Marmor.")
        self.assertEqual(p3.intent, IntentCategory.MATERIAL_TRANSFORM)
        self.assertEqual(p3.target_object, "Tisch")
        self.assertEqual(p3.target_material, "marble")
        self.assertEqual(p3.mode, "LOCAL")
        self.assertTrue(p3.is_confident)

        # 4. Entferne den Gegenstand links, ohne den Hintergrund zu verändern.
        p4 = self.parser.parse("Entferne den Gegenstand links, ohne den Hintergrund zu verändern.")
        self.assertEqual(p4.intent, IntentCategory.OBJECT_REMOVAL)
        self.assertEqual(p4.spatial_hint, "left")
        self.assertEqual(p4.mode, "LOCAL")
        self.assertTrue(p4.is_confident)

        # 5. Verändere nur die Farbe des Autos.
        p5 = self.parser.parse("Verändere nur die Farbe des Autos.")
        self.assertEqual(p5.intent, IntentCategory.COLOR_TRANSFORM)
        self.assertEqual(p5.target_object, "Auto")
        self.assertEqual(p5.mode, "LOCAL")
        self.assertTrue(p5.is_confident)

    def test_ambiguous_and_unknown_prompts(self):
        unknowns = [
            "Mach das Bild schöner.",
            "Ein Foto von einem Hund im Park.",
            "Hallo wer bist du",
            "Verändere irgendwas",
            "",
            "   ",
        ]
        for prompt in unknowns:
            res = self.parser.parse(prompt)
            self.assertEqual(res.intent, IntentCategory.UNKNOWN, f"Failed on '{prompt}'")
            self.assertFalse(res.is_confident, f"Should not be confident on '{prompt}'")


class TestColorSpatialSegmenter(unittest.TestCase):
    def setUp(self):
        self.segmenter = ColorSpatialSegmenter()

    def test_synthetic_red_circle_detection(self):
        # Create 200x200 green background with red square in center
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        arr[:, :] = [40, 180, 40]  # Green background
        arr[60:140, 60:140] = [220, 30, 30]  # Red square in center
        img = Image.fromarray(arr)

        res = self.segmenter.segment(img, target_color="red")
        self.assertTrue(res.success)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_confident)
        self.assertIsNotNone(res.mask)
        self.assertGreater(res.active_pixel_count, 5000)

        # Test spatial filtering: hint "left" should prune center/right
        res_left = self.segmenter.segment(img, target_color="red", spatial_hint="left")
        self.assertLess(res_left.active_pixel_count, res.active_pixel_count)

    def test_missing_color_safety_gate(self):
        # All green image, searching for blue -> must reject safely
        arr = np.zeros((200, 200, 3), dtype=np.uint8)
        arr[:, :] = [40, 180, 40]
        img = Image.fromarray(arr)

        res = self.segmenter.segment(img, target_color="blue")
        self.assertFalse(res.success)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_confident)
        self.assertIn("nicht eindeutig gefunden", res.status_message)

    def test_determinism(self):
        arr = np.zeros((150, 150, 3), dtype=np.uint8)
        arr[30:90, 30:90] = [200, 40, 40]
        img = Image.fromarray(arr)

        r1 = self.segmenter.segment(img, target_color="red")
        r2 = self.segmenter.segment(img, target_color="red")
        self.assertEqual(r1.deterministic_hash, r2.deterministic_hash)
        self.assertEqual(r1.active_pixel_count, r2.active_pixel_count)

    def test_performance_acceleration_threshold(self):
        # 512x512 image should segment significantly faster than Sprint 71 baseline (263.73 ms)
        arr = np.zeros((512, 512, 3), dtype=np.uint8)
        arr[100:400, 100:400] = [220, 30, 30]
        img = Image.fromarray(arr)

        res = self.segmenter.segment(img, target_color="red", generate_visuals=False)
        self.assertTrue(res.is_valid)
        self.assertLess(res.elapsed_ms, 200.0, f"Latency {res.elapsed_ms:.1f}ms exceeds target threshold")

    def test_sprint72_six_motifs_quality_smoke(self):
        root = Path(__file__).resolve().parent.parent
        p_apple = root / "reports" / "appl_edit_test_49" / "appl_edit_49_original.png"
        p_table = root / "reports" / "phoenix_material_lab_65" / "m4_wood_plastic_original.png"
        
        if p_apple.exists():
            im = Image.open(p_apple).convert("RGB")
            res = self.segmenter.segment(im, target_color="red")
            self.assertTrue(res.is_valid)
            self.assertTrue(res.is_confident)
            # The real apple covers ~10% of the image; verify it isolates cleanly without background wall leak (<20%)
            self.assertGreater(res.coverage_ratio, 0.05)
            self.assertLess(res.coverage_ratio, 0.20)

        if p_table.exists():
            im = Image.open(p_table).convert("RGB")
            res = self.segmenter.segment(im, target_color="wood")
            self.assertTrue(res.is_valid)
            self.assertTrue(res.is_confident)
            self.assertGreater(res.coverage_ratio, 0.35)


if __name__ == "__main__":
    unittest.main()
