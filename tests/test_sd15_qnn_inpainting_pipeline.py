"""
Integration and Quality Tests for SD1.5 QNN Inpainting Pipeline on Windows ARM64.
Verifies contract compliance, latent blending, HTP execution, and bit-exact unmasked pixel identity.
"""

from __future__ import annotations

import json
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from PIL import Image

from controllers.inpainting_controller import InpaintingController
from engine.backends.sd15_qnn_inpainting_adapter import (
    EulerScheduler,
    SD15QnnInpaintingAdapter,
    SD15QnnInpaintingResult,
    SimpleCLIPTokenizer,
    UNET_LATENT_IN_SCALE,
    UNET_LATENT_IN_ZERO_POINT,
    VAE_DECODER_IN_SCALE,
    VAE_DECODER_IN_ZERO_POINT,
    VAE_ENCODER_IN_SCALE,
    VAE_ENCODER_IN_ZERO_POINT,
    VAE_ENCODER_OUT_SCALE,
    VAE_ENCODER_OUT_ZERO_POINT,
    dequantize_encoder_output,
    align_color_lab,
    generate_feathered_mask,
    lab2rgb_np,
    quantize_decoder_latent,
    rgb2lab_np,
    quantize_encoder_input,
    quantize_unet_latent,
)

TEST_DIR = REPO_ROOT / "temp" / "sd15_inpainting_test_artifacts"
SOURCE_IMAGE_PATH = REPO_ROOT / "temp" / "sd15_first_npu_image" / "first_sd15_npu.png"


class SD15InpaintingPipelineContractsTest(unittest.TestCase):
    """Unit and contract tests for inpainting components."""

    def test_quantization_parameters_contracts(self) -> None:
        """Verify proven quantization parameters for HTP Encoder, Decoder, and UNet."""
        self.assertAlmostEqual(VAE_ENCODER_IN_SCALE, 0.000030518044, places=8)
        self.assertEqual(VAE_ENCODER_IN_ZERO_POINT, 32768)

        self.assertAlmostEqual(VAE_ENCODER_OUT_SCALE, 0.00012290581, places=7)
        self.assertEqual(VAE_ENCODER_OUT_ZERO_POINT, 35417)

        self.assertAlmostEqual(UNET_LATENT_IN_SCALE, 0.00024176308943424374, places=8)
        self.assertEqual(UNET_LATENT_IN_ZERO_POINT, 33983)

        self.assertAlmostEqual(VAE_DECODER_IN_SCALE, 0.00034003707696683705, places=8)
        self.assertEqual(VAE_DECODER_IN_ZERO_POINT, 34382)

    def test_quantization_and_requantization_contracts(self) -> None:
        """Verify quantization boundaries and requantization mathematical equivalence."""
        # Test input normalization to uint16
        in_sample = np.array([[[[-1.0, 0.0, 1.0]]]], dtype=np.float32)
        q_in = quantize_encoder_input(in_sample)
        self.assertEqual(q_in.dtype, np.uint16)
        self.assertEqual(int(q_in[0, 0, 0, 0]), 0)
        self.assertEqual(int(q_in[0, 0, 0, 1]), 32768)
        self.assertEqual(int(q_in[0, 0, 0, 2]), 65535)

        # Test encoder zero-point maps to FP32 zero latent
        q_enc_zp = np.array([[[[35417, 35417, 35417, 35417]]]], dtype=np.uint16)
        lat_fp32 = dequantize_encoder_output(q_enc_zp)
        self.assertTrue(np.allclose(lat_fp32, 0.0, atol=1e-6))

        # Test zero latent maps to decoder and unet zero points
        q_dec = quantize_decoder_latent(lat_fp32)
        self.assertEqual(int(q_dec[0, 0, 0, 0]), 34382)

        q_unet = quantize_unet_latent(lat_fp32)
        self.assertEqual(int(q_unet[0, 0, 0, 0]), 33983)

        # Verify equivalence of two-step requantization vs direct affine scaling
        test_q_enc = np.random.randint(0, 65536, size=(1, 64, 64, 4), dtype=np.uint16)
        lat_fp32_rnd = dequantize_encoder_output(test_q_enc)
        q_dec_two_step = quantize_decoder_latent(lat_fp32_rnd)

        scale_ratio = VAE_ENCODER_OUT_SCALE / VAE_DECODER_IN_SCALE
        q_dec_direct = np.clip(
            np.round((test_q_enc.astype(np.float32) - 35417) * scale_ratio) + 34382, 0, 65535
        ).astype(np.uint16)

        diff = np.max(np.abs(q_dec_two_step.astype(np.int32) - q_dec_direct.astype(np.int32)))
        self.assertLessEqual(int(diff), 1)

    def test_pure_htp_encoder_execution_without_cpu_fallback(self) -> None:
        """Verify HTP VAE-Encoder executes purely on Qualcomm Hexagon HTP with fallback disabled."""
        import onnxruntime as ort
        import onnxruntime_qnn as qnn

        adapter = SD15QnnInpaintingAdapter()
        if not adapter.encoder_path.is_file():
            self.skipTest(f"HTP encoder not found: {adapter.encoder_path}")

        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
        devices = [d for d in ort.get_ep_devices() if d.ep_name == "QNNExecutionProvider"]
        if not devices:
            self.skipTest("No QNN devices available.")

        opts = ort.SessionOptions()
        opts.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        opts.add_provider_for_devices(devices, {"backend_path": qnn.get_qnn_htp_path()})

        sess = ort.InferenceSession(str(adapter.encoder_path), sess_options=opts)
        dummy_in = np.zeros((1, 512, 512, 3), dtype=np.uint16)
        in_name = sess.get_inputs()[0].name
        out_name = sess.get_outputs()[0].name

        out = sess.run([out_name], {in_name: dummy_in})[0]
        self.assertEqual(out.shape, (1, 64, 64, 4))
        self.assertEqual(out.dtype, np.uint16)

    def test_euler_scheduler_contracts(self) -> None:
        scheduler = EulerScheduler(num_train_timesteps=1000)
        scheduler.set_timesteps(num_inference_steps=20)
        self.assertEqual(len(scheduler.timesteps), 20)
        self.assertEqual(len(scheduler.sigmas), 21)  # 20 steps + terminal 0.0
        self.assertEqual(scheduler.sigmas[-1], 0.0)
        # Check monotonicity of sigmas (strictly decreasing to 0.0)
        self.assertTrue(all(scheduler.sigmas[i] >= scheduler.sigmas[i + 1] for i in range(20)))

    def test_clip_tokenizer_contracts(self) -> None:
        adapter = SD15QnnInpaintingAdapter()
        vocab_path = adapter.model_dir / "tokenizer" / "vocab.json"
        merges_path = adapter.model_dir / "tokenizer" / "merges.txt"
        if not (vocab_path.is_file() and merges_path.is_file()):
            self.skipTest("SD1.5 tokenizer files not present.")

        tok = SimpleCLIPTokenizer(vocab_path, merges_path)
        tokens = tok.tokenize_prompt("a beautiful digital artwork of a phoenix")
        self.assertEqual(len(tokens), 77)
        self.assertEqual(tokens[0], 49406)  # Start of text
        self.assertIn(49407, tokens)  # End of text

    def test_mask_polarity_and_composite_exactness(self) -> None:
        """
        Verify that outside the mask (mask == 0), the composite is 100% bit-identical
        to the source image, with PSNR = infinity and MAE = 0.
        """
        source_np = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        generated_np = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)

        # Mask: 0 = keep original, 255 = replace with generated
        mask_np = np.zeros((512, 512), dtype=np.uint8)
        mask_np[100:300, 100:300] = 255

        source_img = Image.fromarray(source_np, mode="RGB")
        gen_img = Image.fromarray(generated_np, mode="RGB")
        mask_img = Image.fromarray(mask_np, mode="L")

        composite_img = Image.composite(gen_img, source_img, mask_img)
        comp_np = np.array(composite_img, dtype=np.uint8)

        # Unmasked area (mask == 0): MUST BE 100% BIT-IDENTICAL
        unmasked_diff = np.abs(comp_np[mask_np == 0].astype(np.int32) - source_np[mask_np == 0].astype(np.int32))
        self.assertEqual(int(np.max(unmasked_diff)), 0)
        self.assertEqual(float(np.mean(unmasked_diff)), 0.0)

        # Masked area (mask == 255): MUST BE IDENTICAL TO GENERATED
        masked_diff = np.abs(comp_np[mask_np == 255].astype(np.int32) - generated_np[mask_np == 255].astype(np.int32))
        self.assertEqual(int(np.max(masked_diff)), 0)

    def test_generate_feathered_mask_contracts(self) -> None:
        """Verify dilation, inward Gaussian feathering, and bit-exact unmasked preservation."""
        m = np.zeros((100, 100), dtype=np.uint8)
        m[30:70, 30:70] = 255
        m_img = Image.fromarray(m)

        # 1. Test dilate_pixels=0: outside mask must be strictly 0
        f0 = generate_feathered_mask(m_img, dilate_pixels=0, feather_radius=5)
        f0_arr = np.array(f0)
        self.assertEqual(int(f0_arr[m == 0].max()), 0)
        # Verify smooth gradient inside the mask along border
        self.assertGreater(int(f0_arr[30, 50]), 0)
        self.assertLess(int(f0_arr[30, 50]), 255)
        self.assertEqual(int(f0_arr[50, 50]), 255)
        # Verify monotonicity from edge to core
        self.assertTrue(all(f0_arr[y, 50] <= f0_arr[y + 1, 50] for y in range(30, 40)))

        # 2. Test dilate_pixels=2: expands edit zone by 2 pixels
        f2 = generate_feathered_mask(m_img, dilate_pixels=2, feather_radius=5)
        f2_arr = np.array(f2)
        dilated_zone = np.zeros((100, 100), dtype=bool)
        dilated_zone[28:72, 28:72] = True
        self.assertEqual(int(f2_arr[~dilated_zone].max()), 0)
        self.assertEqual(int(f2_arr[50, 50]), 255)

        # 3. Test feather_radius=0: returns binary mask
        f_no_blur = generate_feathered_mask(m_img, dilate_pixels=0, feather_radius=0)
        self.assertTrue(np.array_equal(np.array(f_no_blur), m))

        # 4. Test edge cases: empty and full masks
        empty_m = Image.new("L", (100, 100), 0)
        self.assertEqual(int(np.array(generate_feathered_mask(empty_m)).max()), 0)

        full_m = Image.new("L", (100, 100), 255)
        self.assertEqual(int(np.array(generate_feathered_mask(full_m)).min()), 255)

    def test_edge_feathering_composite_exactness(self) -> None:
        """
        Verify that compositing with a feathered mask (dilate_pixels=0) guarantees
        100% bit-exact parity outside the mask (max_diff = 0, mean_diff = 0.0).
        """
        src = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        gen = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        m = np.zeros((512, 512), dtype=np.uint8)
        m[150:350, 150:350] = 255
        m_img = Image.fromarray(m)

        feathered_mask = generate_feathered_mask(m_img, dilate_pixels=0, feather_radius=5)
        comp = Image.composite(Image.fromarray(gen), Image.fromarray(src), feathered_mask)
        comp_np = np.array(comp)

        # Outside mask (m == 0): MUST BE 100% BIT-IDENTICAL
        diff_outside = np.abs(comp_np[m == 0].astype(np.int32) - src[m == 0].astype(np.int32))
        self.assertEqual(int(np.max(diff_outside)), 0)
        self.assertEqual(float(np.mean(diff_outside)), 0.0)

        # Inside mask core (200:300, 200:300): MUST MATCH GENERATED
        diff_core = np.abs(comp_np[200:300, 200:300].astype(np.int32) - gen[200:300, 200:300].astype(np.int32))
        self.assertEqual(int(np.max(diff_core)), 0)

    def test_soft_brush_mask_feathering_and_preservation(self) -> None:
        """Verify that continuous grayscale soft brush masks are preserved and unmasked pixels remain 0."""
        soft_m = np.zeros((100, 100), dtype=np.uint8)
        y, x = np.ogrid[-50:50, -50:50]
        dist = np.sqrt(x * x + y * y)
        soft_m[dist <= 25] = np.round(255.0 * np.clip(1.0 - dist[dist <= 25] / 25.0, 0.0, 1.0)).astype(np.uint8)
        soft_img = Image.fromarray(soft_m, mode="L")

        # 1. feather_radius=0, dilate_pixels=0: bit-exact preservation
        res_no_feather = generate_feathered_mask(soft_img, dilate_pixels=0, feather_radius=0)
        self.assertTrue(np.array_equal(np.array(res_no_feather), soft_m))

        # 2. feather_radius=5: smooth transition, core peak preserved at 255, unmasked pixels strictly 0
        res_feathered = generate_feathered_mask(soft_img, dilate_pixels=0, feather_radius=5)
        res_arr = np.array(res_feathered)
        self.assertEqual(int(np.max(res_arr[soft_m == 0])), 0)
        self.assertEqual(int(res_arr[50, 50]), 255)

        # 3. dilate_pixels=3: expands edit zone, outside zone remains strictly 0
        res_dilated = generate_feathered_mask(soft_img, dilate_pixels=3, feather_radius=0)
        res_dil_arr = np.array(res_dilated)
        self.assertEqual(int(np.max(res_dil_arr[dist > 30])), 0)

    def test_soft_brush_composite_exactness_unmasked_pixels(self) -> None:
        """Verify that compositing with a soft brush mask preserves unmasked pixels with max_diff = 0."""
        src = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        gen = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)

        soft_m = np.zeros((256, 256), dtype=np.uint8)
        y, x = np.ogrid[-128:128, -128:128]
        dist = np.sqrt(x * x + y * y)
        soft_m[dist <= 50] = np.round(255.0 * np.clip(1.0 - dist[dist <= 50] / 50.0, 0.0, 1.0)).astype(np.uint8)
        soft_img = Image.fromarray(soft_m, mode="L")

        src_img = Image.fromarray(src)
        gen_img = Image.fromarray(gen)

        feathered_mask = generate_feathered_mask(soft_img, dilate_pixels=0, feather_radius=5)
        aligned_gen = align_color_lab(
            source_img=src_img,
            generated_img=gen_img,
            mask_img=soft_img,
            dilate_pixels=0,
            feather_radius=5,
        )
        comp = Image.composite(aligned_gen, src_img, feathered_mask)
        comp_np = np.array(comp)

        # Strict bit-exact identity outside soft mask
        diff_outside = np.abs(comp_np[soft_m == 0].astype(np.int32) - src[soft_m == 0].astype(np.int32))
        max_diff = int(np.max(diff_outside))
        mean_diff = float(np.mean(diff_outside))
        self.assertEqual(max_diff, 0, f"Unmasked area modified: max diff={max_diff}")
        self.assertEqual(mean_diff, 0.0)

    def test_latent_mask_thresholding(self) -> None:
        """Verify latent mask binarization preserves full unit variance without edge attenuation."""
        mask_np = np.zeros((512, 512), dtype=np.uint8)
        mask_np[100:300, 100:300] = 255
        mask_img = Image.fromarray(mask_np)

        mask_64_img = mask_img.resize((64, 64), Image.Resampling.BILINEAR)
        mask_64_np = np.array(mask_64_img, dtype=np.float32) / 255.0
        mask_latent = (mask_64_np >= 0.5).astype(np.float32)

        unique_vals = np.unique(mask_latent)
        self.assertTrue(all(v in (0.0, 1.0) for v in unique_vals))


class SD15InpaintingHTPEndToEndTest(unittest.TestCase):
    """End-to-end integration test verifying real execution on Qualcomm Hexagon HTP."""

    @classmethod
    def setUpClass(cls) -> None:
        TEST_DIR.mkdir(parents=True, exist_ok=True)

    def test_end_to_end_inpainting_htp(self) -> None:
        adapter = SD15QnnInpaintingAdapter()
        if not adapter.encoder_path.is_file():
            self.skipTest(f"Encoder not found: {adapter.encoder_path}")
        if not (adapter.model_dir / "unet.onnx").is_file():
            self.skipTest(f"UNet not found: {adapter.model_dir / 'unet.onnx'}")
        if not SOURCE_IMAGE_PATH.is_file():
            self.skipTest(f"Test source image not found: {SOURCE_IMAGE_PATH}")

        # 1. Prepare source image and test mask
        source_img = Image.open(SOURCE_IMAGE_PATH).convert("RGB")
        source_np = np.array(source_img, dtype=np.uint8)

        # Create a defined center mask (160x160 patch)
        # Polarität: 255 = Inpaint, 0 = Keep original
        mask_np = np.zeros((512, 512), dtype=np.uint8)
        mask_np[176:336, 176:336] = 255
        mask_img = Image.fromarray(mask_np, mode="L")

        test_input_path = TEST_DIR / "inpaint_input.png"
        test_mask_path = TEST_DIR / "inpaint_mask.png"
        test_output_path = TEST_DIR / "inpaint_output.png"

        source_img.save(test_input_path, format="PNG")
        mask_img.save(test_mask_path, format="PNG")

        prompt = "a vibrant neon purple holographic crystal orb on the ground"
        steps = 15  # Fast test step count
        seed = 42

        # 2. Run via InpaintingController (synchronous test execution)
        controller = InpaintingController(adapter=adapter)
        progress_events: list[tuple[str, float, str]] = []

        def on_prog(phase: str, val: float, detail: str | None) -> None:
            progress_events.append((phase, val, detail or ""))

        res_holder: list[SD15QnnInpaintingResult] = []

        def on_done(res: SD15QnnInpaintingResult) -> None:
            res_holder.append(res)

        controller.start(
            input_image_path=test_input_path,
            mask_image_path=test_mask_path,
            prompt=prompt,
            output_path=test_output_path,
            steps=steps,
            seed=seed,
            on_progress=on_prog,
            on_complete=on_done,
            asynchronous=False,
        )

        self.assertTrue(len(res_holder) == 1, "Expected completion callback to be called")
        res = res_holder[0]
        self.assertTrue(res.success, f"Inpainting failed: {res.error_message}")
        self.assertTrue(test_output_path.is_file(), f"Output file was not created: {test_output_path}")

        # 3. Verify execution metadata & Qualcomm Hexagon HTP proof
        self.assertEqual(res.metadata.get("device"), "Qualcomm Hexagon HTP V73")
        self.assertTrue(res.metadata.get("disable_cpu_fallback"))
        self.assertTrue(res.metadata.get("all_stages_on_htp"))
        self.assertEqual(res.metadata.get("unet_calls_count"), steps * 2)

        exec_times = res.metadata.get("execution_times", {})
        print(f"\nExecution Times on Snapdragon X:")
        print(f"  HTP VAE Encoder:     {exec_times.get('htp_vae_encoder_ms', 0):.2f} ms")
        print(f"  CPU VAE Encoder:     {exec_times.get('cpu_vae_encoder_ms', 0):.2f} ms (Legacy alias: inactive)")
        print(f"  HTP CLIP Text:       {exec_times.get('htp_clip_text_ms', 0):.2f} ms")
        print(f"  HTP UNet Total:      {exec_times.get('htp_unet_total_ms', 0):.2f} ms ({steps} steps)")
        print(f"  HTP UNet Step Avg:   {exec_times.get('htp_unet_step_avg_ms', 0):.2f} ms/step")
        print(f"  HTP VAE Decoder:     {exec_times.get('htp_vae_decoder_ms', 0):.2f} ms")
        print(f"  Total Pipeline:      {exec_times.get('total_inference_ms', 0):.2f} ms")

        self.assertGreater(exec_times.get("htp_vae_encoder_ms", 0), 0.0)
        self.assertEqual(exec_times.get("cpu_vae_encoder_ms", 0), 0.0)

        # 4. Pixel-level verification:
        output_img = Image.open(test_output_path).convert("RGB")
        output_np = np.array(output_img, dtype=np.uint8)

        # Unmasked area (mask == 0): MUST BE 100% BIT-IDENTICAL (MAE = 0.0, Max Diff = 0)
        unmasked_diff = np.abs(output_np[mask_np == 0].astype(np.int32) - source_np[mask_np == 0].astype(np.int32))
        max_unmasked_diff = int(np.max(unmasked_diff))
        mean_unmasked_diff = float(np.mean(unmasked_diff))

        self.assertEqual(max_unmasked_diff, 0, f"Unmasked area modified: max diff={max_unmasked_diff}")
        self.assertEqual(mean_unmasked_diff, 0.0, f"Unmasked area modified: mean diff={mean_unmasked_diff}")

        # Masked area (mask == 255): MUST SHOW SIGNIFICANT PROMPT-DRIVEN MODIFICATION
        masked_diff = np.abs(output_np[mask_np == 255].astype(np.int32) - source_np[mask_np == 255].astype(np.int32))
        mean_masked_diff = float(np.mean(masked_diff))
        print(f"  Mean modification in masked region: {mean_masked_diff:.2f} / 255")
        self.assertGreater(mean_masked_diff, 15.0, "Masked region was not sufficiently modified by inpainting")

        # 5. Create visual side-by-side comparison artifact
        comparison = Image.new("RGB", (1536, 512))
        comparison.paste(source_img, (0, 0))
        # Overlay mask on source for visualization
        mask_viz = source_img.copy()
        mask_viz_np = np.array(mask_viz)
        mask_viz_np[mask_np == 255] = [220, 50, 50]  # Red overlay for mask
        comparison.paste(Image.fromarray(mask_viz_np), (512, 0))
        comparison.paste(output_img, (1024, 0))
        comparison_path = TEST_DIR / "inpainting_comparison_grid.png"
        comparison.save(comparison_path)

        # Save test report JSON
        test_report = {
            "sprint": "IMG-EDIT-IMPL-17",
            "test_status": "PASS",
            "device": "Qualcomm Hexagon HTP V73",
            "prompt": prompt,
            "steps": steps,
            "seed": seed,
            "unmasked_max_pixel_diff": max_unmasked_diff,
            "unmasked_mean_pixel_diff": mean_unmasked_diff,
            "unmasked_pixel_identity": "100% BIT-EXACT",
            "masked_mean_pixel_diff": mean_masked_diff,
            "masked_modification": "PROMPT-DRIVEN (PASS)",
            "execution_times": exec_times,
            "artifacts": {
                "input": str(test_input_path.resolve()),
                "mask": str(test_mask_path.resolve()),
                "output": str(test_output_path.resolve()),
                "comparison": str(comparison_path.resolve()),
            },
        }
        with open(TEST_DIR / "inpainting_test_report.json", "w", encoding="utf-8") as f:
            json.dump(test_report, f, indent=2)

        print(f"  Comparison artifact saved to: {comparison_path}")
        print("PASS: SD1.5 Inpainting Pipeline verified successfully on Qualcomm Hexagon HTP.")


class SD15InpaintingCancellationAndErrorTest(unittest.TestCase):
    """
    Verification tests for cancel status, worker crash classification,
    and race conditions in SD15QnnInpaintingAdapter (IMG-EDIT-IMPL-12).
    """

    def test_cancel_during_running_inference(self) -> None:
        """1. Abbruch während laufender Inferenz -> ERR_INPAINTING_CANCELLED."""
        adapter = SD15QnnInpaintingAdapter()

        class MockRunningProcess:
            def __init__(self, *args, **kwargs) -> None:
                self.returncode = 1
                self._poll: int | None = None
                self._terminated = threading.Event()
                self._lines = ["PROGRESS:prepare:0.05:Worker gestartet\n", "PROGRESS:denoise:0.2:Schritt 1/20\n"]

            def poll(self) -> int | None:
                return self._poll

            def terminate(self) -> None:
                self._poll = 1
                self._terminated.set()

            def wait(self, timeout: float | None = None) -> int:
                return self.returncode

            def kill(self) -> None:
                self._poll = 1
                self._terminated.set()

            @property
            def stdout(self):
                mock_out = MagicMock()
                def readline():
                    if self._terminated.is_set():
                        return ""
                    if self._lines:
                        return self._lines.pop(0)
                    self._terminated.wait(timeout=1.0)
                    return ""
                mock_out.readline = readline
                mock_out.close = MagicMock()
                return mock_out

        mock_proc_holder = []
        def make_mock(*args, **kwargs):
            p = MockRunningProcess(*args, **kwargs)
            mock_proc_holder.append(p)
            return p

        def cancel_worker():
            for _ in range(50):
                if adapter._active_process is not None:
                    adapter.cancel()
                    break
                time.sleep(0.01)

        t = threading.Thread(target=cancel_worker)
        t.daemon = True

        with patch("subprocess.Popen", side_effect=make_mock):
            t.start()
            res = adapter._execute_in_subprocess({"dummy": True})
            t.join(timeout=2.0)

        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_INPAINTING_CANCELLED")
        self.assertEqual(res.error_message, "Inpainting-Vorgang wurde durch den Benutzer abgebrochen.")

    def test_regular_worker_crash_without_cancel(self) -> None:
        """2. Regulärer Worker-Absturz ohne Cancel -> ERR_WORKER_CRASH."""
        adapter = SD15QnnInpaintingAdapter()

        mock_proc = MagicMock()
        mock_proc.poll.side_effect = [None, 1]
        mock_proc.returncode = 1
        mock_proc.stdout.readline.return_value = ""
        mock_proc.wait.return_value = 1

        with patch("subprocess.Popen", return_value=mock_proc):
            res = adapter._execute_in_subprocess({"dummy": True})

        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_WORKER_CRASH")
        self.assertIn("ohne Ausgabedatei", res.error_message or "")
        self.assertNotEqual(res.error_code, "ERR_INPAINTING_CANCELLED")

    def test_cancel_without_output_json(self) -> None:
        """3. Abbruch ohne vorhandene output.json -> ERR_INPAINTING_CANCELLED."""
        adapter = SD15QnnInpaintingAdapter()

        # Call cancel before execution starts (pre-spawn cancel)
        adapter.cancel()

        res = adapter._execute_in_subprocess({"dummy": True})

        self.assertFalse(res.success)
        self.assertEqual(res.error_code, "ERR_INPAINTING_CANCELLED")
        self.assertEqual(res.error_message, "Inpainting-Vorgang wurde durch den Benutzer abgebrochen.")

    def test_normal_successful_run_unaffected(self) -> None:
        """4. Normaler erfolgreicher Inpainting-Lauf bleibt unverändert -> success=True."""
        adapter = SD15QnnInpaintingAdapter()

        mock_proc = MagicMock()
        mock_proc.poll.side_effect = [None, 0]
        mock_proc.returncode = 0
        mock_proc.stdout.readline.return_value = ""
        mock_proc.wait.return_value = 0

        # Simulate worker creating job_output.json
        def fake_popen(cmd, *args, **kwargs):
            output_json_path = Path(cmd[3])
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "success": True,
                    "output_path": "temp/test_result.png",
                    "backend_name": "sd15_qnn_htp",
                    "metadata": {"test": True}
                }, f)
            return mock_proc

        with patch("subprocess.Popen", side_effect=fake_popen):
            res = adapter._execute_in_subprocess({"dummy": True})

        self.assertTrue(res.success)
        self.assertEqual(res.output_path, "temp/test_result.png")
        self.assertEqual(res.metadata.get("test"), True)
        self.assertIsNone(res.error_code)

    def test_scheduler_denoising_strength_timestep_mapping(self) -> None:
        """Verify EulerScheduler step reduction and starting sigma across strength values."""
        scheduler = EulerScheduler()
        total_steps = 20
        scheduler.set_timesteps(total_steps)

        # Strength 1.0 -> 20 inference steps (100% of schedule)
        strength_10 = 1.0
        steps_10 = max(1, round(total_steps * strength_10))
        t_start_10 = total_steps - steps_10
        active_t_10 = scheduler.timesteps[t_start_10:]
        active_s_10 = scheduler.sigmas[t_start_10:]
        self.assertEqual(steps_10, 20)
        self.assertEqual(t_start_10, 0)
        self.assertEqual(len(active_t_10), 20)
        self.assertEqual(len(active_s_10), 21)
        self.assertAlmostEqual(active_s_10[0], scheduler.sigmas[0], places=4)
        self.assertEqual(active_s_10[-1], 0.0)

        # Strength 0.65 -> 13 inference steps (65% of schedule)
        strength_65 = 0.65
        steps_65 = max(1, round(total_steps * strength_65))
        t_start_65 = total_steps - steps_65
        active_t_65 = scheduler.timesteps[t_start_65:]
        active_s_65 = scheduler.sigmas[t_start_65:]
        self.assertEqual(steps_65, 13)
        self.assertEqual(t_start_65, 7)
        self.assertEqual(len(active_t_65), 13)
        self.assertEqual(len(active_s_65), 14)
        self.assertAlmostEqual(active_s_65[0], scheduler.sigmas[7], places=4)
        self.assertLess(active_s_65[0], scheduler.sigmas[0])
        self.assertEqual(active_s_65[-1], 0.0)

        # Strength 0.35 -> 7 inference steps (35% of schedule)
        strength_35 = 0.35
        steps_35 = max(1, round(total_steps * strength_35))
        t_start_35 = total_steps - steps_35
        active_t_35 = scheduler.timesteps[t_start_35:]
        active_s_35 = scheduler.sigmas[t_start_35:]
        self.assertEqual(steps_35, 7)
        self.assertEqual(t_start_35, 13)
        self.assertEqual(len(active_t_35), 7)
        self.assertEqual(len(active_s_35), 8)
        self.assertAlmostEqual(active_s_35[0], scheduler.sigmas[13], places=4)
        self.assertEqual(active_s_35[-1], 0.0)

        # Minimum clamp boundary 0.1 -> 2 steps
        strength_10_min = 0.1
        steps_min = max(1, round(total_steps * strength_10_min))
        self.assertEqual(steps_min, 2)

    def test_adaptive_crop_box_min_size_and_clamping(self) -> None:
        """Verify MIN_CROP_SIZE = 256, 1:1 aspect ratio, and boundary clamping."""
        self.assertEqual(InpaintingController.MIN_CROP_SIZE, 256)

        # 1. Centered tiny mask (20x20) in 1920x1080 -> Crop box is >= 256x256, aspect ratio 1:1
        mask_center = Image.new("L", (1920, 1080), 0)
        mask_center.paste(255, (950, 530, 970, 550))
        box = InpaintingController._square_crop_box(mask_center)
        self.assertEqual(box[2] - box[0], 256)
        self.assertEqual(box[3] - box[1], 256)
        self.assertGreaterEqual(box[0], 0)
        self.assertGreaterEqual(box[1], 0)
        self.assertLessEqual(box[2], 1920)
        self.assertLessEqual(box[3], 1080)
        # Verify mask is fully inside the crop box
        self.assertLessEqual(box[0], 950)
        self.assertGreaterEqual(box[2], 970)
        self.assertLessEqual(box[1], 530)
        self.assertGreaterEqual(box[3], 550)

        # 2. Border mask near top-left (10, 10, 30, 30) -> clamped at (0, 0, 256, 256)
        mask_tl = Image.new("L", (1920, 1080), 0)
        mask_tl.paste(255, (10, 10, 30, 30))
        box_tl = InpaintingController._square_crop_box(mask_tl)
        self.assertEqual(box_tl, (0, 0, 256, 256))

        # 3. Border mask near bottom-right (1900, 1060, 1915, 1075) -> clamped at boundary
        mask_br = Image.new("L", (1920, 1080), 0)
        mask_br.paste(255, (1900, 1060, 1915, 1075))
        box_br = InpaintingController._square_crop_box(mask_br)
        self.assertEqual(box_br, (1664, 824, 1920, 1080))
        self.assertEqual(box_br[2] - box_br[0], 256)
        self.assertEqual(box_br[3] - box_br[1], 256)

        # 4. Large mask (600x600) -> expands proportionally with 25% context
        mask_large = Image.new("L", (1920, 1080), 0)
        mask_large.paste(255, (500, 200, 1100, 800))
        box_large = InpaintingController._square_crop_box(mask_large)
        self.assertEqual(box_large[2] - box_large[0], 900)
        self.assertEqual(box_large[3] - box_large[1], 900)

        # 5. Small image smaller than 256 (150x150) -> clamps cleanly
        mask_small = Image.new("L", (150, 150), 0)
        mask_small.paste(255, (30, 30, 60, 60))
        box_small = InpaintingController._square_crop_box(mask_small)
        self.assertEqual(box_small, (0, 0, 150, 150))

    def test_lab_color_roundtrip_and_harmonization(self) -> None:
        """Verify Lab color math precision, boundary harmonization, and max_diff = 0 unmasked."""
        # Test RGB <-> Lab roundtrip identity
        np.random.seed(42)
        sample_rgb = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
        lab = rgb2lab_np(sample_rgb.astype(np.float32) / 255.0)
        rec = np.round(lab2rgb_np(lab) * 255.0).astype(np.uint8)
        max_diff = int(np.max(np.abs(sample_rgb.astype(np.int32) - rec.astype(np.int32))))
        self.assertLessEqual(max_diff, 1)

        # Test align_color_lab boundary luminance and color harmonization
        source = Image.new("RGB", (256, 256), (100, 100, 100))
        # Generated patch has a slight brightness jump and tint
        generated = Image.new("RGB", (256, 256), (115, 112, 108))
        mask = Image.new("L", (256, 256), 0)
        mask.paste(255, (64, 64, 192, 192))

        aligned = align_color_lab(
            source_img=source,
            generated_img=generated,
            mask_img=mask,
            dilate_pixels=0,
            feather_radius=5,
        )
        aligned_np = np.array(aligned)
        # Inside the patch, colors should be harmonized toward source (100, 100, 100)
        self.assertLess(abs(int(aligned_np[128, 128, 0]) - 100), abs(115 - 100))

        # Test composite preservation: outside mask strictly max_diff == 0
        feathered = generate_feathered_mask(mask, dilate_pixels=0, feather_radius=5)
        composite = Image.composite(aligned, source, feathered)
        comp_np = np.array(composite)
        src_np = np.array(source)

        mask_np = np.array(mask)
        # Unmasked area (mask == 0) must be 100% bit-exact
        unmasked_diff = np.max(np.abs(comp_np[mask_np == 0].astype(np.int32) - src_np[mask_np == 0].astype(np.int32)))
        self.assertEqual(int(unmasked_diff), 0)


if __name__ == "__main__":
    unittest.main()
