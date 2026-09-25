from __future__ import annotations

import ast
from pathlib import Path
import unittest

import numpy as np


RUNNER = Path(__file__).parents[1] / "engine" / "backends" / "fidesr_strong_runner_template.py"


def load_cleanup():
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    names = {
        "CPU_POST_STRIPE_ROWS",
        "DUST_RING_RADIUS",
        "DUST_SOURCE_CONTRAST_MIN",
        "DUST_RESTORED_CONTRAST_MIN",
        "DUST_AMPLIFICATION_MIN",
        "DUST_COMPONENT_MAX_PIXELS",
        "DUST_COMPONENT_MAX_SPAN",
        "DUST_COMPONENT_MIN_FILL",
        "DUST_PROTECTION_MARGIN",
        "DUST_TEXTURE_GRADIENT_MIN",
        "DUST_TEXTURE_DENSITY_MAX",
        "DUST_SOURCE_DETAIL_DENSITY_MAX",
        "DUST_STRUCTURE_GRADIENT_MIN",
        "DUST_STRUCTURE_COHERENCE_MAX",
        "DUST_OUTPUT_BRIGHT_MIN",
        "DUST_OUTPUT_DARK_MAX",
        "DUST_RECONSTRUCTION_MARGIN",
        "DUST_RECONSTRUCTION_HALO",
        "DUST_RECONSTRUCTION_BORDER",
        "DUST_RECONSTRUCTION_HALO_CONTRAST_MIN",
        "DUST_RECONSTRUCTION_HALO_AMPLIFICATION_MIN",
        "DUST_RECONSTRUCTION_SOURCE_OUTPUT_DELTA_MIN",
        "DUST_RECONSTRUCTION_EDGE_ENERGY_MIN",
        "DUST_RECONSTRUCTION_EDGE_COHERENCE_MIN",
    }
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in names
            for target in node.targets
        ):
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "apply_source_anchored_dust_cleanup":
            nodes.append(node)
    namespace = {"np": np}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(RUNNER), "exec"), namespace)
    return namespace["apply_source_anchored_dust_cleanup"]


class FiDeSRSourceAnchoredDustCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cleanup = staticmethod(load_cleanup())

    @staticmethod
    def flat_pair(size: int = 41):
        source = np.full((size, size, 3), 0.30, dtype=np.float32)
        restored = np.full((size, size, 3), 0.30, dtype=np.float32)
        return source, restored

    def test_source_anchored_amplified_point_is_reduced(self) -> None:
        source, restored = self.flat_pair()
        source[20, 20] = 0.58
        restored[20, 20] = 1.0
        cleaned, changed = self.cleanup(restored, source)
        self.assertTrue(changed[20, 20])
        self.assertAlmostEqual(float(cleaned[20, 20, 0]), 0.30, places=5)

    def test_multiple_isolated_defects_are_reduced(self) -> None:
        source, restored = self.flat_pair(81)
        for y, x, source_value, restored_value in (
            (20, 20, 0.58, 1.0),
            (20, 60, 0.12, 0.0),
            (60, 40, 0.55, 0.92),
        ):
            source[y, x] = source_value
            restored[y, x] = restored_value
        cleaned, changed = self.cleanup(restored, source)
        self.assertTrue(all(changed[y, x] for y, x in ((20, 20), (20, 60), (60, 40))))
        self.assertLess(float(cleaned[20, 20, 0]), 1.0)
        self.assertGreater(float(cleaned[20, 60, 0]), 0.0)

    def test_small_two_by_three_fleck_is_reduced(self) -> None:
        source, restored = self.flat_pair()
        source[19:21, 19:22] = 0.55
        restored[19:21, 19:22] = 0.95
        cleaned, changed = self.cleanup(restored, source)
        self.assertTrue(changed[19:21, 19:22].all())
        np.testing.assert_allclose(cleaned[19:21, 19:22], 0.30, atol=1e-6)

    def test_dark_fleck_is_reduced(self) -> None:
        source, restored = self.flat_pair()
        source[19:22, 19:22] = 0.12
        restored[19:22, 19:22] = 0.0
        cleaned, changed = self.cleanup(restored, source)
        self.assertTrue(changed[19:22, 19:22].all())
        self.assertAlmostEqual(float(cleaned[20, 20, 0]), 0.30, places=5)

    def test_small_irregular_spot_is_reduced(self) -> None:
        source, restored = self.flat_pair(61)
        points = ((27, 29), (28, 28), (28, 29), (28, 30), (29, 29), (30, 29))
        for y, x in points:
            source[y, x] = 0.50
            restored[y, x] = 0.82
        cleaned, changed = self.cleanup(restored, source)
        self.assertTrue(any(changed[y, x] for y, x in points))
        self.assertLess(float(np.mean(cleaned[[y for y, _ in points], [x for _, x in points], 0])), 0.50)

    def test_defect_near_edge_preserves_edge_continuity(self) -> None:
        source = np.empty((41, 41, 3), dtype=np.float32)
        restored = np.empty_like(source)
        source[:, :21] = 0.20
        source[:, 21:] = 0.70
        restored[:] = source
        source[19:22, 19:21] = 0.52
        restored[19:22, 19:21] = 1.0
        cleaned, changed = self.cleanup(restored, source)
        self.assertTrue(changed[19:22, 19:21].all())
        np.testing.assert_allclose(cleaned[19:22, 19:21], 0.20, atol=1e-6)
        np.testing.assert_array_equal(cleaned[:, 21:], restored[:, 21:])

    def test_output_only_point_is_not_removed(self) -> None:
        source, restored = self.flat_pair()
        restored[20, 20] = 1.0
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_hair_like_line_is_preserved(self) -> None:
        source, restored = self.flat_pair()
        source[20, 12:29] = 0.05
        restored[20, 12:29] = 0.0
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_stubble_and_pore_cluster_is_preserved(self) -> None:
        source, restored = self.flat_pair()
        points = [(17, 17), (17, 21), (20, 19), (22, 22), (23, 17), (19, 24)]
        for y, x in points:
            source[y, x] = 0.08
            restored[y, x] = 0.0
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_pore_cluster_is_preserved(self) -> None:
        source, restored = self.flat_pair()
        for y in range(15, 27, 2):
            for x in range(15, 27, 2):
                source[y, x] = 0.12
                restored[y, x] = 0.0
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_grass_and_leaf_texture_is_preserved(self) -> None:
        source, restored = self.flat_pair(51)
        for offset in range(8, 43, 4):
            source[8:43, offset] = 0.10
            restored[8:43, offset] = 0.0
            source[offset, 8:43] = 0.50
            restored[offset, 8:43] = 0.68
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_foliage_texture_is_preserved(self) -> None:
        source, restored = self.flat_pair(61)
        yy, xx = np.ogrid[:61, :61]
        for cy, cx in ((20, 20), (20, 36), (36, 20), (36, 36)):
            leaf = ((yy - cy) ** 2 / 20 + (xx - cx) ** 2 / 45) <= 1
            source[leaf] = 0.16
            restored[leaf] = 0.05
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_textile_weave_is_preserved(self) -> None:
        source, restored = self.flat_pair(61)
        for y in range(10, 51, 4):
            source[y:y + 1, 10:51] = 0.20
            restored[y:y + 1, 10:51] = 0.08
        for x in range(10, 51, 4):
            source[10:51, x:x + 1] = 0.44
            restored[10:51, x:x + 1] = 0.58
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_real_dark_compact_content_is_preserved(self) -> None:
        source, restored = self.flat_pair(61)
        yy, xx = np.ogrid[:61, :61]
        content = ((yy - 30) ** 2 + (xx - 30) ** 2) <= 36
        source[content] = 0.08
        restored[content] = 0.02
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_wood_grain_and_fine_edges_are_preserved(self) -> None:
        source, restored = self.flat_pair(51)
        for x in range(7, 44, 5):
            source[7:44, x:x + 2] = 0.14
            restored[7:44, x:x + 2] = 0.02
        source[24:27, 7:44] = 0.48
        restored[24:27, 7:44] = 0.68
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_texture_rich_region_is_preserved(self) -> None:
        source, restored = self.flat_pair()
        for y in range(12, 29):
            for x in range(12, 29):
                value = 0.12 if (x + y) % 2 else 0.48
                source[y, x] = value
                restored[y, x] = 0.0 if value < 0.30 else 0.70
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_large_compact_reflection_is_preserved(self) -> None:
        source, restored = self.flat_pair()
        source[17:24, 17:24] = 0.62
        restored[17:24, 17:24] = 1.0
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())

    def test_outside_reported_roi_is_bit_exact(self) -> None:
        source, restored = self.flat_pair()
        source[20, 20] = 0.58
        restored[20, 20] = 1.0
        baseline = restored.copy()
        cleaned, changed = self.cleanup(restored, source)
        self.assertGreater(int(np.count_nonzero(changed)), 0)
        self.assertEqual(int(np.count_nonzero(cleaned[~changed] != baseline[~changed])), 0)

    def test_no_candidate_is_exact_noop(self) -> None:
        rng = np.random.default_rng(20260924)
        source = rng.uniform(0.25, 0.35, size=(41, 41, 3)).astype(np.float32)
        restored = source.copy()
        cleaned, changed = self.cleanup(restored, source)
        np.testing.assert_array_equal(cleaned, restored)
        self.assertFalse(changed.any())


if __name__ == "__main__":
    unittest.main()
