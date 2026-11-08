"""Unit and contract tests for SD1.5 VAE Encoder."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import unittest
from types import SimpleNamespace

import numpy as np
import torch

from tools.export_sd15_vae_encoder import (
    INPUT_SHAPE,
    OUTPUT_SHAPE,
    SCALING_FACTOR,
    OPSET_VERSION,
    SD15VAEEncoderExportWrapper,
    DEFAULT_TARGET_ONNX,
    DEFAULT_VALIDATION_DIR,
)


class SD15VAEEncoderContractTests(unittest.TestCase):
    def test_fixed_export_contracts(self) -> None:
        self.assertEqual(INPUT_SHAPE, (1, 3, 512, 512))
        self.assertEqual(OUTPUT_SHAPE, (1, 64, 64, 4))
        self.assertEqual(SCALING_FACTOR, 0.18215)
        self.assertEqual(OPSET_VERSION, 17)

    def test_wrapper_computes_deterministic_mean_scale_and_nhwc(self) -> None:
        # Create a mock VAE where encoder outputs [1, 8, 64, 64] and quant_conv is identity
        class MockEncoder(torch.nn.Module):
            def forward(self, x: torch.Tensor) -> torch.Tensor:
                # Fill 8 channels: channels 0-3 with value 2.0, channels 4-7 with value 99.0 (logvar)
                out = torch.zeros(1, 8, 64, 64, dtype=torch.float32)
                out[:, 0:4, :, :] = 2.0
                out[:, 4:8, :, :] = 99.0
                return out

        class MockQuantConv(torch.nn.Module):
            def forward(self, x: torch.Tensor) -> torch.Tensor:
                return x * 1.0  # pass-through

        mock_vae = SimpleNamespace(
            encoder=MockEncoder(),
            quant_conv=MockQuantConv(),
        )

        wrapper = SD15VAEEncoderExportWrapper(mock_vae, scaling_factor=SCALING_FACTOR)
        dummy_input = torch.zeros(INPUT_SHAPE, dtype=torch.float32)

        actual_output = wrapper(dummy_input)

        # Expected:
        # 1. Takes channels 0:4 (value 2.0)
        # 2. Multiplies by 0.18215 -> 0.3643
        # 3. Permutes to [1, 64, 64, 4] (NHWC)
        self.assertEqual(tuple(actual_output.shape), OUTPUT_SHAPE)
        expected_value = 2.0 * SCALING_FACTOR
        expected_tensor = torch.full(OUTPUT_SHAPE, expected_value, dtype=torch.float32)
        torch.testing.assert_close(actual_output, expected_tensor, rtol=1e-5, atol=1e-5)

    def test_wrapper_is_strictly_deterministic(self) -> None:
        class RandomMockEncoder(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.weight = torch.nn.Parameter(torch.randn(8, 3, 3, 3))

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                return torch.nn.functional.conv2d(x, self.weight, padding=1)

        class IdentityConv(torch.nn.Module):
            def forward(self, x: torch.Tensor) -> torch.Tensor:
                return x

        mock_vae = SimpleNamespace(encoder=RandomMockEncoder(), quant_conv=IdentityConv())
        wrapper = SD15VAEEncoderExportWrapper(mock_vae, scaling_factor=SCALING_FACTOR).eval()

        inp = torch.randn(INPUT_SHAPE, dtype=torch.float32)
        with torch.no_grad():
            out1 = wrapper(inp)
            out2 = wrapper(inp)

        torch.testing.assert_close(out1, out2, rtol=0.0, atol=0.0)

    def test_exported_onnx_parity_if_present(self) -> None:
        if not DEFAULT_TARGET_ONNX.is_file():
            self.skipTest("ONNX artifact not yet exported.")

        import onnxruntime as ort

        sess = ort.InferenceSession(str(DEFAULT_TARGET_ONNX), providers=["CPUExecutionProvider"])
        self.assertEqual(sess.get_inputs()[0].name, "image")
        self.assertEqual(sess.get_inputs()[0].shape, list(INPUT_SHAPE))
        self.assertEqual(sess.get_outputs()[0].name, "latent")
        self.assertEqual(sess.get_outputs()[0].shape, list(OUTPUT_SHAPE))

        # Check against reference fixture if available
        input_fixture = DEFAULT_VALIDATION_DIR / "vae_input_sample.npy"
        ref_fixture = DEFAULT_VALIDATION_DIR / "vae_latent_reference.npy"
        if input_fixture.is_file() and ref_fixture.is_file():
            x = np.load(input_fixture)
            expected = np.load(ref_fixture)
            actual = sess.run(["latent"], {"image": x})[0]
            max_err = float(np.max(np.abs(actual - expected)))
            mean_err = float(np.mean(np.abs(actual - expected)))
            corr = float(np.corrcoef(actual.flatten().astype(np.float64), expected.flatten().astype(np.float64))[0, 1])
            self.assertLess(max_err, 0.015)
            self.assertLess(mean_err, 1e-3)
            self.assertGreater(corr, 0.99999)


if __name__ == "__main__":
    unittest.main()
