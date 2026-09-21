from __future__ import annotations

import ast
from pathlib import Path
import unittest

import numpy as np
from PIL import Image


RUNNER = Path(__file__).parents[1] / "engine" / "backends" / "fidesr_strong_runner_template.py"


def load_optimized_functions():
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    function_names = {
        "percentile_norm",
        "conv3_same_rep",
        "detail_map_from_rgb",
        "wavelet_blur",
        "wavelet_decomposition",
        "wavelet_high",
        "wavelet_low",
        "apply_detail_preservation_bypass",
    }
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in function_names:
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "CPU_POST_STRIPE_ROWS"
            for target in node.targets
        ):
            nodes.append(node)
    namespace = {"np": np, "Image": Image}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(RUNNER), "exec"), namespace)
    return namespace


def legacy_wavelet_blur(image, radius):
    kernel = np.array(
        [[0.0625, 0.125, 0.0625], [0.125, 0.25, 0.125], [0.0625, 0.125, 0.0625]],
        dtype=np.float32,
    )
    height, width, _ = image.shape
    padded = np.pad(image, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    result = np.zeros_like(image, dtype=np.float32)
    offsets = (-radius, 0, radius)
    for ky, oy in enumerate(offsets):
        for kx, ox in enumerate(offsets):
            result += padded[
                radius + oy:radius + oy + height,
                radius + ox:radius + ox + width,
                :,
            ] * kernel[ky, kx]
    return result


def legacy_conv3(tensor, kernel):
    padded = np.pad(tensor, ((0, 0), (0, 0), (1, 1), (1, 1)), mode="edge")
    result = np.zeros_like(tensor, dtype=np.float32)
    for ky in range(3):
        for kx in range(3):
            result += padded[
                :, :, ky:ky + tensor.shape[2], kx:kx + tensor.shape[3]
            ] * float(kernel[ky, kx])
    return result


def legacy_detail_map(image, percentile_norm):
    rgb = image.astype(np.float32) * 0.5 + 0.5
    gray = 0.299 * rgb[:, 0:1] + 0.587 * rgb[:, 1:2] + 0.114 * rgb[:, 2:3]
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    laplace = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    box = np.ones((3, 3), dtype=np.float32) / 9.0
    ex = legacy_conv3(gray, sobel_x)
    ey = legacy_conv3(gray, sobel_y)
    sobel = np.sqrt(ex * ex + ey * ey)
    laplace_magnitude = np.abs(legacy_conv3(gray, laplace))
    mean = legacy_conv3(gray, box)
    variance = legacy_conv3((gray - mean) ** 2, box)
    detail = percentile_norm((sobel + laplace_magnitude + variance) / 3.0)
    return legacy_conv3(detail, box)


def legacy_wavelet(image, levels=5):
    current = image.astype(np.float32).copy()
    high = np.zeros_like(current, dtype=np.float32)
    for level in range(levels):
        low = legacy_wavelet_blur(current, 2 ** level)
        high += current - low
        current = low
    return high, current


def legacy_detail(base, source):
    import torch
    import torch.nn.functional as functional

    base_t = torch.tensor(base, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
    source_t = torch.tensor(source, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
    y_base = 0.299 * base_t[:, 0:1] + 0.587 * base_t[:, 1:2] + 0.114 * base_t[:, 2:3]
    cb = -0.168736 * base_t[:, 0:1] - 0.331264 * base_t[:, 1:2] + 0.5 * base_t[:, 2:3] + 0.5
    cr = 0.5 * base_t[:, 0:1] - 0.418688 * base_t[:, 1:2] - 0.081312 * base_t[:, 2:3] + 0.5
    y_source = 0.299 * source_t[:, 0:1] + 0.587 * source_t[:, 1:2] + 0.114 * source_t[:, 2:3]

    def blur(tensor, sigma):
        size = int(2 * round(3 * sigma) + 1)
        if size % 2 == 0:
            size += 1
        coords = torch.arange(size, dtype=torch.float32) - (size - 1) / 2.0
        gaussian = torch.exp(-(coords**2) / (2.0 * sigma**2))
        gaussian = gaussian / gaussian.sum()
        kernel = (gaussian.unsqueeze(1) * gaussian.unsqueeze(0)).unsqueeze(0).unsqueeze(0)
        return functional.conv2d(tensor, kernel, padding=size // 2)

    def local_std(tensor, size=7):
        mean = functional.avg_pool2d(tensor, size, stride=1, padding=size // 2)
        mean_sq = functional.avg_pool2d(tensor**2, size, stride=1, padding=size // 2)
        return torch.sqrt(torch.clamp(mean_sq - mean**2, min=0.0))

    bp_source = blur(y_source, 0.6) - blur(y_source, 1.8)
    bp_base = blur(y_base, 0.6) - blur(y_base, 1.8)
    std_source = local_std(bp_source)
    deficit = torch.clamp(std_source - local_std(bp_base), min=0.0) / (std_source + 1e-4)
    gx = y_base[:, :, :, 1:] - y_base[:, :, :, :-1]
    gy = y_base[:, :, 1:, :] - y_base[:, :, :-1, :]
    gradient = torch.zeros_like(y_base)
    gradient[:, :, :-1, :-1] = torch.sqrt(gx[:, :, :-1, :]**2 + gy[:, :, :, :-1]**2)
    attenuation = torch.clamp(1.0 - gradient / 0.12, min=0.0, max=1.0)
    y_out = torch.clamp(y_base + 0.85 * deficit * attenuation * bp_source, 0.0, 1.0)
    cb -= 0.5
    cr -= 0.5
    result = torch.clamp(
        torch.cat(
            [y_out + 1.402 * cr, y_out - 0.344136 * cb - 0.714136 * cr, y_out + 1.772 * cb],
            dim=1,
        ),
        0.0,
        1.0,
    )
    return result[0].permute(1, 2, 0).numpy()


class FiDeSRPostprocessRamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.optimized = load_optimized_functions()

    def test_striped_wavelet_is_bit_exact(self):
        image = np.random.default_rng(20260920).random((273, 37, 3), dtype=np.float32)
        expected_high, expected_low = legacy_wavelet(image)
        actual_high, actual_low = self.optimized["wavelet_decomposition"](image)
        np.testing.assert_array_equal(actual_high, expected_high)
        np.testing.assert_array_equal(actual_low, expected_low)
        np.testing.assert_array_equal(self.optimized["wavelet_high"](image), expected_high)
        np.testing.assert_array_equal(self.optimized["wavelet_low"](image), expected_low)

    def test_striped_detail_map_is_bit_exact(self):
        rng = np.random.default_rng(20260920)
        image = (rng.random((1, 3, 273, 37)) * 2.0 - 1.0).astype(np.float16)
        expected = legacy_detail_map(image, self.optimized["percentile_norm"])
        actual = self.optimized["detail_map_from_rgb"](image)
        np.testing.assert_array_equal(actual, expected)

    def test_striped_detail_bypass_is_bit_exact(self):
        rng = np.random.default_rng(20260920)
        base = rng.random((273, 37, 3), dtype=np.float32)
        source = rng.random((273, 37, 3), dtype=np.float32)
        expected = legacy_detail(base.copy(), source)
        actual = self.optimized["apply_detail_preservation_bypass"](base.copy(), source)
        np.testing.assert_array_equal(actual, expected)


if __name__ == "__main__":
    unittest.main()
