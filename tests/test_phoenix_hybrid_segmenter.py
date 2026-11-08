"""
Unit tests for Phoenix Hybrid Segmentation Engine (Sprint 95).
Validates fusion logic, sub-object isolation, negative point subtraction,
and backward-compatible SegmentResult conversion.
"""

import unittest
from unittest.mock import MagicMock
import numpy as np
from PIL import Image

from engine.phoenix_hybrid_segmenter import PhoenixHybridSegmenter, HybridSegmentResult
from engine.color_spatial_segmenter import SegmentResult


class TestPhoenixHybridSegmenter(unittest.TestCase):
    """Test suite for PhoenixHybridSegmenter logic and safety gates."""

    def setUp(self):
        # Create test synthetic image: 100x100 RGB
        self.test_img = Image.new("RGB", (100, 100), color=(50, 50, 50))
        # Draw a red rectangle (apparel) at [20, 20, 80, 80]
        for y in range(20, 80):
            for x in range(20, 80):
                self.test_img.putpixel((x, y), (220, 20, 20))

    def test_initialization(self):
        """Verify default and customized initialization."""
        segmenter = PhoenixHybridSegmenter(enable_htp=False)
        self.assertFalse(segmenter.enable_htp)
        self.assertIsNotNone(segmenter.color_segmenter)
        self.assertIsNone(segmenter.sam_adapter)

    def test_mock_sam_hybrid_fusion(self):
        """Verify semantic mask and color mask fusion with positive point."""
        mock_sam = MagicMock()
        # Mock SAM mask: 100x100 boolean array covering [10, 10, 90, 90] (entire body)
        sam_mask = np.zeros((100, 100), dtype=bool)
        sam_mask[10:90, 10:90] = True
        mock_sam.predict_mask.return_value = (sam_mask, 0.98)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=self.test_img,
            point_prompt=(50, 50),
            target_object_hint="jacket",
            target_color_hint="rot",
            protect_skin=True,
            generate_visuals=True,
        )

        self.assertTrue(res.success)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_confident)
        self.assertIsNotNone(res.mask)
        self.assertIsNotNone(res.overlay_image)
        self.assertIsNotNone(res.comparison_grid)
        self.assertAlmostEqual(res.confidence_score, 0.98, places=2)
        # Sub-object formula should isolate the red region and not bleed to [10, 10, 90, 90]
        mask_arr = np.array(res.mask)
        self.assertTrue(mask_arr[50, 50] > 0)
        self.assertEqual(mask_arr[15, 15], 0)  # Outside red rectangle

    def test_negative_point_exclusion(self):
        """Verify negative point removes excluded region from segmentation."""
        mock_sam = MagicMock()
        sam_mask = np.zeros((100, 100), dtype=bool)
        sam_mask[20:80, 20:80] = True
        mock_sam.predict_mask.return_value = (sam_mask, 0.95)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        # Add negative point inside the red region at (50, 50) with radius
        res = segmenter.segment_hybrid(
            image=self.test_img,
            point_prompt=(30, 30),
            negative_points=[(50, 50)],
            target_object_hint="shape",
            protect_skin=False,
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        mask_arr = np.array(res.mask)
        # Seed positive point should remain selected
        self.assertTrue(mask_arr[30, 30] > 0)
        # Negative point location should be 0 (subtracted)
        self.assertEqual(mask_arr[50, 50], 0)

    def test_multi_object_disambiguation(self):
        """Verify that clicking one of two identical objects isolates only the clicked one."""
        # Create canvas with two red boxes: left [10:40, 10:40] and right [60:90, 60:90]
        multi_img = Image.new("RGB", (100, 100), color=(20, 20, 20))
        for y in range(10, 40):
            for x in range(10, 40):
                multi_img.putpixel((x, y), (230, 30, 30))
        for y in range(60, 90):
            for x in range(60, 90):
                multi_img.putpixel((x, y), (230, 30, 30))

        mock_sam = MagicMock()
        # SAM mask covers left box only
        left_sam_mask = np.zeros((100, 100), dtype=bool)
        left_sam_mask[10:40, 10:40] = True
        mock_sam.predict_mask.return_value = (left_sam_mask, 0.96)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=multi_img,
            point_prompt=(25, 25),
            target_object_hint="box",
            protect_skin=False,
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        mask_arr = np.array(res.mask)
        # Left box must be selected
        self.assertTrue(mask_arr[25, 25] > 0)
        # Right box must have 0.00% leakage
        right_box_pixels = mask_arr[60:90, 60:90]
        self.assertEqual(int(right_box_pixels.sum()), 0)

    def test_cavity_preservation(self):
        """Verify cavity in a donut-shaped object is 0 when negative point is inside cavity."""
        donut_img = Image.new("RGB", (100, 100), color=(240, 240, 240))
        # Draw blue donut: outer box [20:80, 20:80], cavity [40:60, 40:60]
        for y in range(20, 80):
            for x in range(20, 80):
                if 40 <= x < 60 and 40 <= y < 60:
                    continue  # Cavity (background color)
                donut_img.putpixel((x, y), (30, 120, 220))

        mock_sam = MagicMock()
        donut_sam_mask = np.zeros((100, 100), dtype=bool)
        donut_sam_mask[20:80, 20:80] = True  # SAM accidentally filled cavity
        mock_sam.predict_mask.return_value = (donut_sam_mask, 0.94)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=donut_img,
            point_prompt=(30, 30),  # On foreground ring
            negative_points=[(50, 50)],  # Inside cavity
            target_object_hint="ring",
            protect_skin=False,
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        mask_arr = np.array(res.mask)
        # Foreground ring is active
        self.assertTrue(mask_arr[30, 30] > 0)
        # Cavity center (50, 50) is cleanly 0
        self.assertEqual(mask_arr[50, 50], 0)

    def test_sam_failure_graceful_fallback(self):
        """Verify seamless fallback to ColorSpatialSegmenter when SAM raises an exception."""
        mock_sam = MagicMock()
        mock_sam.predict_mask.side_effect = RuntimeError("HTP execution interrupted")
        mock_sam.set_image.side_effect = RuntimeError("HTP device busy")

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=self.test_img,
            point_prompt=(50, 50),
            target_object_hint="box",
            target_color_hint="rot",
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        self.assertIsNotNone(res.mask)
        mask_arr = np.array(res.mask)
        self.assertTrue(mask_arr[50, 50] > 0)

    def test_to_dict_serialization(self):
        """Verify telemetry dictionary contains all required Phoenix metrics."""
        result = HybridSegmentResult(
            success=True,
            is_valid=True,
            is_confident=True,
            active_pixel_count=1234,
            coverage_ratio=0.1234,
            coverage_percentage=12.34,
            spatial_bbox=[10, 10, 50, 50],
            detected_color_name="rot",
            status_message="OK",
            deterministic_hash="abc123hash",
            elapsed_ms=45.67,
            mobile_sam_latency_ms=12.34,
            confidence_score=0.95,
            sub_object_isolated=True,
            hardware_target="Qualcomm Hexagon NPU (HTP V73)",
            cpu_fallback_count=0,
        )
        d = result.to_dict()
        self.assertEqual(d["active_pixel_count"], 1234)
        self.assertEqual(d["hardware_target"], "Qualcomm Hexagon NPU (HTP V73)")
        self.assertEqual(d["cpu_fallback_count"], 0)
        self.assertEqual(d["sub_object_isolated"], True)
        self.assertIn("confidence_score", d)
        self.assertIn("raw_iou_score", d)

    def test_background_click_triggers_safety_gate_2(self):
        """Sprint 97: Verify background click outside candidate object triggers Safety Gate 2."""
        mock_sam = MagicMock()
        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        # Test image has red box at [20:80, 20:80]. Clicking at (5, 5) is pure background.
        res = segmenter.segment_hybrid(
            image=self.test_img,
            point_prompt=(5, 5),
            target_object_hint="box",
            target_color_hint="rot",
            generate_visuals=False,
        )
        self.assertFalse(res.success)
        self.assertFalse(res.is_valid)
        self.assertFalse(res.is_confident)
        self.assertEqual(res.active_pixel_count, 0)
        self.assertIn("Safety Gate 2", res.status_message)
        # SAM should not even have been called
        mock_sam.predict_mask.assert_not_called()

    def test_biological_tissue_protection_neck_and_face(self):
        """Sprint 97: Verify biological tissue protection eliminates face/neck pixels up to Y=240."""
        # Create portrait mockup (512x512)
        h, w = 512, 512
        port_img = Image.new("RGB", (w, h), (240, 240, 240))
        # Draw head/face at [100:220, 200:310] with warm skin tone
        for y in range(100, 220):
            for x in range(200, 310):
                port_img.putpixel((x, y), (225, 145, 105))
        # Draw neck at [220:240, 220:290] with warm skin tone
        for y in range(220, 240):
            for x in range(220, 290):
                port_img.putpixel((x, y), (220, 140, 100))
        # Draw jacket at [240:420, 160:350] with red tone
        for y in range(240, 420):
            for x in range(160, 350):
                port_img.putpixel((x, y), (210, 30, 30))

        mock_sam = MagicMock()
        # Simulated person mask covering head + neck + jacket [100:420, 160:350]
        sam_person = np.zeros((h, w), dtype=bool)
        sam_person[100:420, 160:350] = True
        mock_sam.predict_mask.return_value = (sam_person, 0.99)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=port_img,
            point_prompt=(256, 310),
            target_object_hint="jacket",
            target_color_hint="rot",
            protect_skin=True,
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        mask_arr = np.array(res.mask) > 127
        # Strict requirement: 0 face pixels and 0 neck pixels in Y < 240
        face_neck_leakage = int(mask_arr[:240, :].sum())
        self.assertEqual(face_neck_leakage, 0)
        # Jacket body in Y >= 240 must be actively selected
        jacket_body_pixels = int(mask_arr[240:, :].sum())
        self.assertGreater(jacket_body_pixels, 5000)

    def test_full_cavity_protection_radius_40(self):
        """Sprint 97: Verify complete cavity clearance without 15px radius limitation."""
        w, h = 200, 200
        star_img = Image.new("RGB", (w, h), (245, 245, 245))
        # Blue star body with radius 80
        for y in range(h):
            for x in range(w):
                d_sq = (x - 100) ** 2 + (y - 100) ** 2
                if d_sq <= 80 ** 2 and d_sq > 40 ** 2:
                    star_img.putpixel((x, y), (0, 180, 255))
                # Cavity inside radius 40 remains background color (245, 245, 245)

        mock_sam = MagicMock()
        # Mock SAM accidentally filling the cavity
        sam_solid = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                if (x - 100) ** 2 + (y - 100) ** 2 <= 80 ** 2:
                    sam_solid[y, x] = True
        mock_sam.predict_mask.return_value = (sam_solid, 0.95)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=star_img,
            point_prompt=(100, 30),  # On star body
            negative_points=[(100, 100)],  # Center of cavity (radius 40)
            target_object_hint="star",
            protect_skin=False,
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        mask_arr = np.array(res.mask) > 127
        # Full cavity circle of radius 40
        y_idx, x_idx = np.ogrid[:h, :w]
        cavity_circle = (x_idx - 100) ** 2 + (y_idx - 100) ** 2 <= (40 ** 2)
        cavity_leakage = int(np.logical_and(mask_arr, cavity_circle).sum())
        self.assertEqual(cavity_leakage, 0)

    def test_raw_iou_and_confidence_separation(self):
        """Sprint 97: Verify raw IoU score > 1.0 is preserved while confidence is clamped to <= 1.0."""
        mock_sam = MagicMock()
        sam_mask = np.zeros((100, 100), dtype=bool)
        sam_mask[20:80, 20:80] = True
        # Model emits raw unconstrained score > 1.0
        mock_sam.predict_mask.return_value = (sam_mask, 1.0425)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=self.test_img,
            point_prompt=(50, 50),
            target_object_hint="box",
            target_color_hint="rot",
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        self.assertEqual(res.raw_iou_score, 1.0425)
        self.assertEqual(res.confidence_score, 1.0)
        self.assertLessEqual(res.confidence_score, 1.0)
        telemetry = res.to_dict()
        self.assertEqual(telemetry["raw_iou_score"], 1.0425)
        self.assertEqual(telemetry["confidence_score"], 1.0)

    def test_zero_outer_spillover_freeform_star(self):
        """Sprint 101: Verify exact 0px outer spillover and 0 cavity leakage on freeform star."""
        import math
        w, h = 512, 512
        freeform_img = Image.new("RGB", (w, h), (245, 245, 245))
        from PIL import ImageDraw
        draw_ff = ImageDraw.Draw(freeform_img)
        cx, cy = 256, 256
        R_out, R_in = 160, 70
        num_points = 5
        star_pts = []
        for i in range(num_points * 2):
            r = R_out if i % 2 == 0 else R_in
            angle = i * math.pi / num_points - math.pi / 2
            star_pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw_ff.polygon(star_pts, fill=(0, 180, 255))
        R_cavity = 40
        draw_ff.ellipse([cx - R_cavity, cy - R_cavity, cx + R_cavity, cy + R_cavity], fill=(245, 245, 245))

        # Ground Truth
        gt_img = Image.new("L", (w, h), 0)
        draw_gt = ImageDraw.Draw(gt_img)
        draw_gt.polygon(star_pts, fill=255)
        draw_gt.ellipse([cx - R_cavity, cy - R_cavity, cx + R_cavity, cy + R_cavity], fill=0)
        gt_arr = np.array(gt_img) > 127

        mock_sam = MagicMock()
        # Mock SAM spilling into background canvas
        sam_mask = np.zeros((h, w), dtype=bool)
        sam_mask[80:420, 80:420] = True
        mock_sam.predict_mask.return_value = (sam_mask, 0.96)
        mock_sam.set_image.return_value = np.zeros((1, 256, 64, 64), dtype=np.float32)

        segmenter = PhoenixHybridSegmenter(sam_adapter=mock_sam, enable_htp=True)
        res = segmenter.segment_hybrid(
            image=freeform_img,
            point_prompt=(256, 120),
            negative_points=[(256, 256)],
            target_object_hint="star",
            protect_skin=False,
            generate_visuals=False,
        )

        self.assertTrue(res.success)
        final_arr = np.array(res.mask) > 127
        # Verify 0 outer spillover
        fp_pixels = int(np.logical_and(final_arr, ~gt_arr).sum())
        self.assertEqual(fp_pixels, 0)
        # Verify cavity clearance
        y_idx, x_idx = np.ogrid[:h, :w]
        cavity_circle = (x_idx - 256) ** 2 + (y_idx - 256) ** 2 <= (R_cavity ** 2)
        cavity_leakage = int(np.logical_and(final_arr, cavity_circle).sum())
        self.assertEqual(cavity_leakage, 0)
        # Verify high foreground retention
        tp_pixels = int(np.logical_and(final_arr, gt_arr).sum())
        self.assertGreater(tp_pixels, 28000)


if __name__ == "__main__":
    unittest.main()
