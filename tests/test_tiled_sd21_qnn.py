from __future__ import annotations

import unittest

import numpy as np

from engine.experiments.tiled_sd21_qnn import (
    accumulate_tiles,
    cosine_blend_mask,
    create_global_latents,
    create_tile_plan,
)


class TiledSD21QnnTests(unittest.TestCase):
    def test_tile_positions_are_deterministic_and_boundary_aligned(self) -> None:
        plan = create_tile_plan(overlap=8)
        self.assertEqual((0, 56, 64), tuple(sorted({position.x for position in plan.positions})))
        self.assertEqual((0, 56, 64), tuple(sorted({position.y for position in plan.positions})))
        self.assertEqual(9, len(plan.positions))
        for position in plan.positions:
            self.assertGreaterEqual(position.x, 0)
            self.assertGreaterEqual(position.y, 0)
            self.assertLessEqual(position.x + position.width, plan.canvas_width)
            self.assertLessEqual(position.y + position.height, plan.canvas_height)

    def test_complete_canvas_coverage_for_both_overlaps(self) -> None:
        for overlap in (8, 16):
            plan = create_tile_plan(overlap=overlap)
            coverage = np.zeros((plan.canvas_height, plan.canvas_width), dtype=bool)
            for position in plan.positions:
                coverage[position.y : position.y + position.height, position.x : position.x + position.width] = True
            self.assertTrue(coverage.all())

    def test_cosine_mask_is_soft_positive_and_bounded(self) -> None:
        plan = create_tile_plan(overlap=16)
        interior = plan.positions[4]
        mask = cosine_blend_mask(plan, interior)
        self.assertEqual((64, 64), mask.shape)
        self.assertGreater(float(mask.min()), 0.0)
        self.assertLess(float(mask[0, 0]), 1.0)
        self.assertEqual(1.0, float(mask[32, 32]))
        self.assertLessEqual(float(mask.max()), 1.0)

    def test_accumulator_has_positive_weights_and_blends_constants(self) -> None:
        plan = create_tile_plan(overlap=8)
        tiles = [np.full((1, 64, 64, 4), index, dtype=np.float32) for index, _ in enumerate(plan.positions)]
        blended, weights = accumulate_tiles(plan, tiles)
        self.assertEqual((1, 128, 128, 4), blended.shape)
        self.assertGreater(float(weights.min()), 0.0)
        self.assertTrue(np.isfinite(blended).all())
        self.assertEqual(0.0, float(blended[0, 0, 0, 0]))
        self.assertEqual(8.0, float(blended[0, -1, -1, 0]))

    def test_global_latent_initialization_is_deterministic(self) -> None:
        first = create_global_latents(123456789)
        second = create_global_latents(123456789)
        different = create_global_latents(123456788)
        np.testing.assert_array_equal(first, second)
        self.assertFalse(np.array_equal(first, different))
        self.assertEqual((1, 128, 128, 4), first.shape)


if __name__ == "__main__":
    unittest.main()
