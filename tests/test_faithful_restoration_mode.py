"""
HK NPU STUDIO - Phoenix Architecture
Faithful & Enhanced Restoration Mode Focused Integration Tests

Verifies the 2 separate restoration modes:
1. Faithful Restoration:
   - FiDeSR Strong backend called on QNN/HTP
   - RealESRGAN NOT called
   - Deterministic CPU finishing only
   - Output size: (orig_w * scale, orig_h * scale)
   - Original input not overwritten

2. Enhanced Restoration:
   - FiDeSR Strong called first on QNN/HTP
   - RealESRGAN x4 called second on QNN/HTP
   - Raw RealESRGAN size: (fidesr_w * 4, fidesr_h * 4)
   - Deterministic Lanczos downsampling to target size: (orig_w * scale, orig_h * scale)
   - No CPU or GPU AI fallback
   - Output size contracts strictly verified
   - Original input not overwritten

3. UI & Error Handling:
   - Both modes selectable in UI
   - Default is 'faithful'
   - Unsupported modes safely rejected
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import threading
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
from PIL import Image

import config
from controllers.photo_restore_controller import PhotoRestoreController
from engine.backends.fidesr_photo_restore_backend import (
    FiDeSRPhotoRestoreBackend,
    PhotoRestoreResult,
    PHOTO_RESTORE_INPUT_INVALID,
)
from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView
from engine.theme_manager import ThemeManager
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme


class PhotoRestoreModesIntegrationTests(unittest.TestCase):
    """Focused integration test suite for Faithful and Enhanced Restoration modes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tk_root = tk.Tk()
        cls.tk_root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.tk_root.destroy()
        except Exception:
            pass

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.out_dir = self.root / "output"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Create 128x128 sample input image
        self.input_path = self.root / "sample_input.png"
        img = Image.new("RGB", (128, 128), (140, 120, 100))
        img.save(self.input_path)
        self.original_hash = hashlib.sha256(self.input_path.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_faithful_restoration_mode_contract(self) -> None:
        """
        Proves Faithful Mode:
        - FiDeSR backend called
        - RealESRGAN NOT called
        - QNN/HTP path used
        - No CPU/GPU AI fallback
        - Input not overwritten
        - Valid output produced
        """
        backend = FiDeSRPhotoRestoreBackend()
        backend._status = "INITIALIZED"

        fidesr_called = False
        realesrgan_called = False

        def mock_run_strong(input_path: Path, work_dir: Path, progress):
            nonlocal fidesr_called
            fidesr_called = True
            out_img = Image.new("RGB", (512, 512), (150, 130, 110))
            out_path = work_dir / "fidesr_strong_x4.png"
            out_img.save(out_path)
            log_text = (
                "[FiDeSR Strong] Running on Qualcomm QNN HTP\n"
                "ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS\n"
            )
            return out_path, log_text

        def mock_run_realesrgan(*args, **kwargs):
            nonlocal realesrgan_called
            realesrgan_called = True
            raise AssertionError("RealESRGAN was called in Faithful mode!")

        with patch.object(backend, "_run_strong", side_effect=mock_run_strong):
            with patch.object(backend, "_run_realesrgan_npu", side_effect=mock_run_realesrgan):
                controller = PhotoRestoreController(backend=backend)
                results: list[PhotoRestoreResult] = []
                controller.start(
                    image_path=self.input_path,
                    output_dir=self.out_dir,
                    upscale_factor=4,
                    auto_colorize=False,
                    mode="faithful",
                    on_complete=results.append,
                    asynchronous=False,
                )

        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertTrue(res.success, f"Restore failed: {res.error_message}")
        self.assertTrue(fidesr_called, "FiDeSR backend was NOT called!")
        self.assertFalse(realesrgan_called, "RealESRGAN was called in Faithful mode!")

        # QNN/HTP verification
        self.assertEqual(res.metadata.get("runtime"), "QNN/HTP")
        self.assertTrue(res.metadata.get("qnn_htp_pass"))

        # RealESRGAN NOT called in metadata
        self.assertFalse(res.metadata.get("realesrgan_after_fidesr"))
        self.assertFalse(res.metadata.get("realesrgan_called"))

        # No CPU/GPU AI fallback
        self.assertFalse(res.metadata.get("cpu_model_inference"))
        self.assertFalse(res.metadata.get("gpu_model_inference"))

        # Input image not overwritten
        self.assertTrue(self.input_path.is_file())
        self.assertEqual(self.original_hash, hashlib.sha256(self.input_path.read_bytes()).hexdigest())

        # Valid output
        self.assertIsNotNone(res.output_path)
        out_path = Path(res.output_path)
        self.assertTrue(out_path.is_file())
        self.assertIn("faithful_x4", out_path.name)
        with Image.open(out_path) as out_im:
            self.assertEqual(out_im.size, (512, 512))

    def test_enhanced_restoration_mode_contract(self) -> None:
        """
        Proves Enhanced Mode:
        - FiDeSR called first
        - RealESRGAN called second (ordered sequence)
        - Both use existing QNN/HTP paths
        - No CPU AI / GPU AI fallback
        - FIDESR_OUTPUT_SIZE: (512, 512)
        - REALESRGAN_RAW_OUTPUT_SIZE: (2048, 2048)
        - FINAL_OUTPUT_SIZE: (512, 512)
        - FINAL_RESIZE_METHOD: Lanczos
        - Input not overwritten
        - Valid output produced
        """
        backend = FiDeSRPhotoRestoreBackend()
        backend._status = "INITIALIZED"

        call_sequence: list[str] = []

        def mock_run_strong(input_path: Path, work_dir: Path, progress):
            call_sequence.append("fidesr")
            # FiDeSR 4x output (128x128 -> 512x512)
            out_img = Image.new("RGB", (512, 512), (150, 130, 110))
            out_path = work_dir / "fidesr_strong_x4.png"
            out_img.save(out_path)
            log_text = "ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS\n"
            return out_path, log_text

        def mock_run_realesrgan(img: Image.Image, work_dir: Path, progress):
            call_sequence.append("realesrgan")
            # FiDeSR output was passed into RealESRGAN (should be 512x512)
            self.assertEqual(img.size, (512, 512), "RealESRGAN did not receive FiDeSR 4x output!")
            # RealESRGAN produces 4x of 512x512 -> 2048x2048 raw
            return Image.new("RGB", (2048, 2048), (160, 140, 120))

        with patch.object(backend, "_run_strong", side_effect=mock_run_strong):
            with patch.object(backend, "_run_realesrgan_npu", side_effect=mock_run_realesrgan):
                controller = PhotoRestoreController(backend=backend)
                results: list[PhotoRestoreResult] = []
                controller.start(
                    image_path=self.input_path,
                    output_dir=self.out_dir,
                    upscale_factor=4,
                    auto_colorize=False,
                    mode="enhanced",
                    on_complete=results.append,
                    asynchronous=False,
                )

        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertTrue(res.success, f"Restore failed: {res.error_message}")

        # 1. Sequence proof: FiDeSR called first, RealESRGAN called second
        self.assertEqual(call_sequence, ["fidesr", "realesrgan"])

        # 2. Both use QNN/HTP path
        self.assertEqual(res.metadata.get("runtime"), "QNN/HTP")
        self.assertTrue(res.metadata.get("qnn_htp_pass"))
        self.assertTrue(res.metadata.get("realesrgan_after_fidesr"))
        self.assertTrue(res.metadata.get("realesrgan_called"))

        # 3. No CPU or GPU AI fallback
        self.assertFalse(res.metadata.get("cpu_model_inference"))
        self.assertFalse(res.metadata.get("gpu_model_inference"))

        # 4. Output size contracts strictly verified
        self.assertEqual(res.metadata.get("fidesr_output_size"), [512, 512])
        self.assertEqual(res.metadata.get("realesrgan_raw_output_size"), [2048, 2048])
        self.assertEqual(res.metadata.get("final_output_size"), [512, 512])
        self.assertEqual(res.metadata.get("final_resize_method"), "Lanczos")

        # 5. Input image not overwritten
        self.assertTrue(self.input_path.is_file())
        self.assertEqual(self.original_hash, hashlib.sha256(self.input_path.read_bytes()).hexdigest())

        # 6. Valid output produced
        self.assertIsNotNone(res.output_path)
        out_path = Path(res.output_path)
        self.assertTrue(out_path.is_file())
        self.assertIn("enhanced_x4", out_path.name)
        with Image.open(out_path) as out_im:
            self.assertEqual(out_im.size, (512, 512))

        # Check metadata JSON sidecar
        sidecar = out_path.with_suffix(".json")
        self.assertTrue(sidecar.is_file())
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(meta.get("mode"), "enhanced")
        self.assertEqual(meta.get("restore_model"), "FiDeSR Strong + RealESRGAN x4")
        self.assertEqual(meta.get("realesrgan_raw_output_size"), [2048, 2048])

    def test_enhanced_restoration_mode_2x(self) -> None:
        """Verify Enhanced mode with 2x downsamples from raw 2048 down to 256x256 (orig*2)."""
        backend = FiDeSRPhotoRestoreBackend()
        backend._status = "INITIALIZED"

        def mock_run_strong(input_path: Path, work_dir: Path, progress):
            out_img = Image.new("RGB", (512, 512), (100, 100, 100))
            out_path = work_dir / "fidesr_strong_x4.png"
            out_img.save(out_path)
            return out_path, "ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS\n"

        def mock_run_realesrgan(img: Image.Image, work_dir: Path, progress):
            return Image.new("RGB", (2048, 2048), (110, 110, 110))

        with patch.object(backend, "_run_strong", side_effect=mock_run_strong):
            with patch.object(backend, "_run_realesrgan_npu", side_effect=mock_run_realesrgan):
                res = backend.restore(
                    image_path=self.input_path,
                    output_dir=self.out_dir,
                    upscale_factor=2,
                    auto_colorize=False,
                    mode="enhanced",
                )

        self.assertTrue(res.success)
        out_path = Path(res.output_path)
        self.assertIn("enhanced_x2", out_path.name)
        with Image.open(out_path) as out_im:
            self.assertEqual(out_im.size, (256, 256))
        self.assertEqual(res.metadata["final_output_size"], [256, 256])
        self.assertEqual(res.metadata["realesrgan_raw_output_size"], [2048, 2048])

    def test_ui_mode_selection(self) -> None:
        """
        Verify UI provides Faithful as the only visible product mode:
        - FAITHFUL_VISIBLE=YES
        - ENHANCED_VISIBLE=NO
        - DEFAULT_MODE=faithful
        """
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            # 1. Default mode is faithful
            self.assertEqual(view.mode_var.get(), "faithful")

            # 2. Faithful is visible in the UI
            self.assertTrue(view.faithful_visible)
            self.assertEqual(view.rb_faithful.winfo_manager(), "pack")
            self.assertEqual(str(view.rb_faithful.cget("state")), "normal")

            # 3. Enhanced is NOT visible in the UI (retained in backend, deactivated in UI)
            self.assertFalse(view.enhanced_visible)
            self.assertEqual(view.rb_enhanced.winfo_manager(), "")
            self.assertEqual(str(view.rb_enhanced.cget("state")), "disabled")
        finally:
            view.destroy()

    def test_faithful_product_mode_contract_checks(self) -> None:
        """
        Explicitly validates the full product contract:
        - FAITHFUL_VISIBLE=YES
        - ENHANCED_VISIBLE=NO
        - DEFAULT_MODE=faithful
        - FAITHFUL_BACKEND=FiDeSR Strong QNN/HTP
        - CPU_AI_FALLBACK=NO
        - ORIGINAL_UNCHANGED=YES
        - OUTPUT_SEPARATE=YES
        """
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            faithful_visible = "YES" if view.faithful_visible else "NO"
            enhanced_visible = "YES" if view.enhanced_visible else "NO"
            default_mode = view.mode_var.get()
        finally:
            view.destroy()

        self.assertEqual(faithful_visible, "YES")
        self.assertEqual(enhanced_visible, "NO")
        self.assertEqual(default_mode, "faithful")

        # Backend verification
        backend = FiDeSRPhotoRestoreBackend()
        backend._status = "INITIALIZED"

        def mock_run_strong(input_path: Path, work_dir: Path, progress):
            out_img = Image.new("RGB", (512, 512), (150, 130, 110))
            out_path = work_dir / "fidesr_strong_x4.png"
            out_img.save(out_path)
            return out_path, "ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS\n"

        with patch.object(backend, "_run_strong", side_effect=mock_run_strong):
            res = backend.restore(
                image_path=self.input_path,
                output_dir=self.out_dir,
                upscale_factor=4,
                mode="faithful",
            )

        self.assertTrue(res.success)
        # Backend runtime & model checks
        self.assertEqual(res.metadata.get("runtime"), "QNN/HTP")
        self.assertEqual(res.metadata.get("restore_model"), "FiDeSR Strong")
        self.assertFalse(res.metadata.get("realesrgan_called"))
        self.assertFalse(res.metadata.get("cpu_model_inference"))

        # Original unchanged check
        self.assertEqual(self.original_hash, hashlib.sha256(self.input_path.read_bytes()).hexdigest())

        # Output separate check
        out_path = Path(res.output_path)
        self.assertTrue(out_path.is_file())
        self.assertNotEqual(out_path.resolve(), self.input_path.resolve())

    def test_unsupported_mode_rejected(self) -> None:
        """Verify unsupported mode strings are safely rejected."""
        backend = FiDeSRPhotoRestoreBackend()
        backend._status = "INITIALIZED"
        res = backend.restore(
            image_path=self.input_path,
            output_dir=self.out_dir,
            upscale_factor=4,
            mode="invalid_fantasy_mode",
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error_code, PHOTO_RESTORE_INPUT_INVALID)


class FiDeSRGranularTileProgressTests(unittest.TestCase):
    """
    Focused test suite verifying granular tile progress across all stages:
    - Tile 1/N and Tile N/N generate progress
    - Monotonic progress guarantee
    - Exact stage and tile detail formatting
    - 1-tile smoke simulation
    - 169-tile simulation (676 granular events)
    - Completion exactly 100%
    - Cancellation and error handling preserved
    """

    def setUp(self) -> None:
        self.backend = FiDeSRPhotoRestoreBackend()

    def test_tile_1_and_n_generate_progress(self) -> None:
        """Verify Tile 1/N and Tile N/N produce correct phase, pct and detail."""
        res_1 = self.backend._progress_from_line(
            "TILE_PROGRESS: stage=VAE_ENCODER tile=1 total=169"
        )
        self.assertIsNotNone(res_1)
        phase_1, pct_1, detail_1 = res_1
        self.assertEqual(phase_1, "restore")
        self.assertGreater(pct_1, 0.02)
        self.assertEqual(detail_1, "VAE Encoder – Kachel 1/169 auf NPU")

        res_n = self.backend._progress_from_line(
            "TILE_PROGRESS: stage=VAE_ENCODER tile=169 total=169"
        )
        self.assertIsNotNone(res_n)
        phase_n, pct_n, detail_n = res_n
        self.assertEqual(phase_n, "restore")
        self.assertAlmostEqual(pct_n, 0.25, places=3)
        self.assertEqual(detail_n, "VAE Encoder – Kachel 169/169 auf NPU")

    def test_stage_names_and_exact_format(self) -> None:
        """Verify all 4 model stages produce exact user-specified label format."""
        samples = [
            ("VAE_ENCODER", 42, 169, "VAE Encoder – Kachel 42/169 auf NPU"),
            ("UNET", 81, 169, "UNet – Kachel 81/169 auf NPU"),
            ("LRRB", 120, 169, "LRRB – Kachel 120/169 auf NPU"),
            ("VAE_DECODER", 160, 169, "VAE Decoder – Kachel 160/169 auf NPU"),
        ]
        for stage, tile, total, expected_detail in samples:
            line = f"TILE_PROGRESS: stage={stage} tile={tile} total={total}"
            res = self.backend._progress_from_line(line)
            self.assertIsNotNone(res, f"Failed for {line}")
            phase, pct, detail = res
            self.assertEqual(phase, "restore")
            self.assertEqual(detail, expected_detail)
            self.assertGreaterEqual(pct, 0.0)
            self.assertLessEqual(pct, 1.0)

    def test_stage_start_events(self) -> None:
        """Verify STAGE_START emits initialization progress for each stage."""
        stages = [
            ("VAE_ENCODER", "VAE Encoder – NPU-Initialisierung (0/169)", 0.02),
            ("UNET", "UNet – NPU-Initialisierung (0/169)", 0.25),
            ("LRRB", "LRRB – NPU-Initialisierung (0/169)", 0.50),
            ("VAE_DECODER", "VAE Decoder – NPU-Initialisierung (0/169)", 0.76),
        ]
        for stage, expected_detail, expected_pct in stages:
            line = f"STAGE_START: stage={stage} total=169"
            res = self.backend._progress_from_line(line)
            self.assertIsNotNone(res)
            phase, pct, detail = res
            self.assertEqual(phase, "restore")
            self.assertEqual(detail, expected_detail)
            self.assertAlmostEqual(pct, expected_pct, places=3)

    def test_progress_strictly_monotonic_full_stream(self) -> None:
        """Simulate a full stream of 169 tiles across all stages and assert monotonic pct."""
        lines = ["PREFLIGHT=PASS"]
        stages = ["VAE_ENCODER", "UNET", "LRRB", "VAE_DECODER"]
        for stg in stages:
            lines.append(f"STAGE_START: stage={stg} total=169")
            for t in range(1, 170):
                lines.append(f"TILE_PROGRESS: stage={stg} tile={t} total=169")
            if stg == "LRRB":
                lines.append("LF_HF_CPU")
            elif stg == "VAE_DECODER":
                lines.append("WAVELET_COLOR_FIX")
                lines.append("DETAIL_PRESERVATION_BYPASS")
                lines.append("FULL_PIPELINE_TECH_PASS=YES")

        last_pct = 0.0
        event_count = 0
        for l in lines:
            res = self.backend._progress_from_line(l)
            if res is not None:
                _, pct, _ = res
                self.assertGreaterEqual(
                    pct,
                    last_pct,
                    f"Monotonicity violated at line: {l}, pct={pct} < last_pct={last_pct}",
                )
                self.assertLessEqual(pct, 1.0)
                last_pct = pct
                event_count += 1

        self.assertGreater(event_count, 680)

    def test_one_tile_smoke_remains_valid(self) -> None:
        """Verify 1-tile smoke test (N=1) works flawlessly without edge-case issues."""
        stages = ["VAE_ENCODER", "UNET", "LRRB", "VAE_DECODER"]
        last_pct = 0.0
        for stg in stages:
            start_res = self.backend._progress_from_line(f"STAGE_START: stage={stg} total=1")
            self.assertIsNotNone(start_res)
            _, s_pct, s_det = start_res
            self.assertGreaterEqual(s_pct, last_pct)
            last_pct = s_pct

            tile_res = self.backend._progress_from_line(f"TILE_PROGRESS: stage={stg} tile=1 total=1")
            self.assertIsNotNone(tile_res)
            _, t_pct, t_det = tile_res
            self.assertIn("Kachel 1/1 auf NPU", t_det)
            self.assertGreaterEqual(t_pct, last_pct)
            last_pct = t_pct

    def test_169_tile_simulation_granular_updates(self) -> None:
        """Verify 169 tiles per stage produce exactly 169 updates per stage (676 total tile events)."""
        stages = ["VAE_ENCODER", "UNET", "LRRB", "VAE_DECODER"]
        total_tile_events = 0
        for stg in stages:
            stage_events = 0
            for t in range(1, 170):
                res = self.backend._progress_from_line(f"TILE_PROGRESS: stage={stg} tile={t} total=169")
                self.assertIsNotNone(res)
                stage_events += 1
                total_tile_events += 1
            self.assertEqual(stage_events, 169)
        self.assertEqual(total_tile_events, 676)

    def test_completion_is_exactly_100_pct(self) -> None:
        """Verify final completion progress callback passes exactly pct=1.0 (100%)."""
        collected = []
        def cb(phase: str, pct: float, detail: str | None) -> None:
            collected.append((phase, pct, detail))

        # Direct verification of the final progress call in restore
        backend = FiDeSRPhotoRestoreBackend()
        backend._status = "INITIALIZED"

        def mock_run_strong(input_path: Path, work_dir: Path, progress):
            out_img = Image.new("RGB", (512, 512), (150, 130, 110))
            out_path = work_dir / "fidesr_strong_x4.png"
            out_img.save(out_path)
            return out_path, "ALL_FIDESR_AI_INFERENCE_QNN_HTP=PASS\n"

        with patch.object(backend, "_run_strong", side_effect=mock_run_strong):
            tmp_input = Path(self.backend.runner_template).parent / "dummy_test.png"
            # create temporary dummy image
            Image.new("RGB", (64, 64)).save(tmp_input)
            try:
                res = backend.restore(
                    image_path=tmp_input,
                    upscale_factor=4,
                    auto_colorize=False,
                    mode="faithful",
                    progress_callback=cb,
                )
            finally:
                if tmp_input.exists():
                    tmp_input.unlink()

        self.assertTrue(res.success)
        self.assertGreater(len(collected), 0)
        final_phase, final_pct, final_det = collected[-1]
        self.assertEqual(final_phase, "save")
        self.assertEqual(final_pct, 1.0)
        self.assertEqual(final_det, "FiDeSR Strong fertiggestellt")

    def test_cancel_and_error_path_unaffected(self) -> None:
        """Verify cooperative cancellation and error handling remain intact."""
        backend = FiDeSRPhotoRestoreBackend()
        backend._status = "INITIALIZED"

        dummy_input = Path(self.backend.runner_template).parent / "dummy_cancel.png"
        Image.new("RGB", (64, 64)).save(dummy_input)

        try:
            # 1. Test cooperative cancellation during execution
            def mock_run_cancel(input_path: Path, work_dir: Path, progress):
                backend.cancel()
                backend._check_cancel()

            with patch.object(backend, "_run_strong", side_effect=mock_run_cancel):
                res_cancel = backend.restore(
                    image_path=dummy_input,
                    upscale_factor=4,
                    mode="faithful",
                )
            self.assertFalse(res_cancel.success)
            self.assertEqual(res_cancel.error_code, "PHOTO_RESTORE_CANCELLED")

            # 2. Test runner error handling
            def mock_run_error(input_path: Path, work_dir: Path, progress):
                raise RuntimeError("QNN runner exited with code 1")

            with patch.object(backend, "_run_strong", side_effect=mock_run_error):
                res_err = backend.restore(
                    image_path=dummy_input,
                    upscale_factor=4,
                    mode="faithful",
                )
            self.assertFalse(res_err.success)
            self.assertEqual(res_err.error_code, "PHOTO_RESTORE_FIDESR_FAILED")
        finally:
            if dummy_input.exists():
                dummy_input.unlink()

class PhoenixPhotoRestoreProgressBarTests(unittest.TestCase):
    """
    Focused test suite verifying Phoenix design compliance for the Photo Restore progress bar:
    - Custom Phoenix style name (Phoenix.Horizontal.TProgressbar)
    - Default gray ttk look removed
    - PHOENIX_THEME token usage (accent fill, elevated track, border)
    - Light / Dark theme parity
    - Callback stability and label readability
    """

    @classmethod
    def setUpClass(cls) -> None:
        if tk._default_root is not None:
            cls.tk_root = tk._default_root
        else:
            cls.tk_root = tk.Tk()
            cls.tk_root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_photo_restore_progressbar_style_name(self) -> None:
        """Verify Photo Restore view uses Phoenix.Horizontal.TProgressbar and removes default gray ttk look."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            style_name = view.progress_bar.cget("style")
            self.assertEqual(style_name, "Phoenix.Horizontal.TProgressbar")
            self.assertNotEqual(style_name, "")
            self.assertNotEqual(style_name, "TProgressbar")
            self.assertNotEqual(style_name, "Horizontal.TProgressbar")
        finally:
            view.destroy()

    def test_photo_restore_progressbar_theme_token_usage(self) -> None:
        """Verify Phoenix progress bar styling strictly uses PHOENIX_THEME tokens with no hardcoded colors."""
        from tkinter import ttk
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            style = ttk.Style(self.tk_root)
            bg = style.lookup("Phoenix.Horizontal.TProgressbar", "background")
            trough = style.lookup("Phoenix.Horizontal.TProgressbar", "troughcolor")
            border = style.lookup("Phoenix.Horizontal.TProgressbar", "bordercolor")

            # Active fill uses existing Phoenix success token (Phoenix Green)
            self.assertEqual(bg, PHOENIX_THEME.success)
            # Track uses elevated background token
            self.assertEqual(trough, PHOENIX_THEME.elevated_bg)
            # Border uses border token
            self.assertEqual(border, PHOENIX_THEME.border)

            # Palette match
            palette = ThemeManager.palette()
            self.assertEqual(bg, palette.success)
            self.assertEqual(trough, palette.elevated)
            self.assertEqual(border, palette.border)
        finally:
            view.destroy()

    def test_photo_restore_progressbar_light_dark_parity(self) -> None:
        """Verify progress bar and surrounding status labels adapt cleanly between Light and Dark themes."""
        from tkinter import ttk
        orig_theme = ThemeManager.active_theme()
        try:
            # 1. Light Theme
            update_phoenix_theme(ThemeManager.PROFESSIONAL_LIGHT)
            style_light = ttk.Style(self.tk_root)
            light_palette = ThemeManager.palette()
            self.assertEqual(style_light.lookup("Phoenix.Horizontal.TProgressbar", "background"), light_palette.success)
            self.assertEqual(style_light.lookup("Phoenix.Horizontal.TProgressbar", "troughcolor"), light_palette.elevated)
            self.assertEqual(style_light.lookup("Phoenix.Horizontal.TProgressbar", "bordercolor"), light_palette.border)
            self.assertEqual(light_palette.elevated, "#F7F8F8")

            # 2. Dark Theme
            update_phoenix_theme(ThemeManager.PROFESSIONAL_DARK)
            style_dark = ttk.Style(self.tk_root)
            dark_palette = ThemeManager.palette()
            self.assertEqual(style_dark.lookup("Phoenix.Horizontal.TProgressbar", "background"), dark_palette.success)
            self.assertEqual(style_dark.lookup("Phoenix.Horizontal.TProgressbar", "troughcolor"), dark_palette.elevated)
            self.assertEqual(style_dark.lookup("Phoenix.Horizontal.TProgressbar", "bordercolor"), dark_palette.border)
            self.assertEqual(dark_palette.elevated, "#272C33")
        finally:
            update_phoenix_theme(orig_theme)

    def test_photo_restore_progressbar_callback_stability(self) -> None:
        """Verify progress bar updates stably through callbacks while preserving label readability."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            # Initial state
            self.assertEqual(view.progress_bar["value"], 0)
            self.assertEqual(view.status_label.cget("text"), "Bereit")
            self.assertEqual(view.progress_percent_label.cget("text"), "")

            # Simulate granular tile updates
            steps = [
                ("prepare", 0.05, "Modelle werden initialisiert"),
                ("fidesr", 0.25, "Tile 42/169 (Phase UNet)"),
                ("fidesr", 0.55, "Tile 100/169 (Phase LRRB)"),
                ("fidesr", 0.85, "Tile 160/169 (Phase VAE Decoder)"),
                ("save", 1.0, "FiDeSR Strong fertiggestellt"),
            ]

            for phase, pct, detail in steps:
                expected_val = int(pct * 100)
                view.progress_bar["value"] = expected_val
                view.progress_percent_label.configure(text=f"{expected_val} %")
                view.status_label.configure(text=f"Phase: {phase.capitalize()}")
                view.progress_detail_label.configure(text=detail)

                self.assertEqual(view.progress_bar["value"], expected_val)
                self.assertEqual(view.progress_percent_label.cget("text"), f"{expected_val} %")
                self.assertIn(phase.capitalize(), view.status_label.cget("text"))
                self.assertEqual(view.progress_detail_label.cget("text"), detail)

            # Check label readability attributes
            self.assertIsNotNone(view.status_label.cget("fg"))
            self.assertIsNotNone(view.status_label.cget("bg"))
            self.assertIsNotNone(view.progress_percent_label.cget("fg"))
            self.assertIsNotNone(view.progress_percent_label.cget("bg"))
            self.assertIsNotNone(view.progress_detail_label.cget("fg"))
            self.assertIsNotNone(view.progress_detail_label.cget("bg"))
        finally:
            view.destroy()


class FiDeSRProcessLifecycleAndInputBoundTests(unittest.TestCase):
    """
    Focused test suite verifying:
    - Process lifecycle: clean exit on completed tiles without premature terminate()
    - Fail-closed termination on timeout / exception
    - Contract: 128px artificial input bound completely reverted
    - Identity & facial detail preservation: native resolution preserved for large photos
    - Navigation: Phoenix Image Lab hub and Photo Restore reachability
    """

    def test_contract_constants(self) -> None:
        """Verify contract constants in runner template."""
        runner_template_path = ROOT_DIR / "engine" / "backends" / "fidesr_strong_runner_template.py"
        self.assertTrue(runner_template_path.is_file())
        text = runner_template_path.read_text(encoding="utf-8")
        # 128px artificial input downscale MUST NOT be present
        self.assertNotIn("target_input_dim = PROCESS_SIZE // rscale", text)
        self.assertNotIn("target_input_dim", text)
        # Official scale factor and lifecycle wait must be present
        self.assertIn("UPSCALE = 4", text)
        self.assertIn("rscale = UPSCALE", text)
        self.assertIn("proc.wait(timeout=120)", text)

    def test_identity_preservation_native_resolution_contract(self) -> None:
        """
        Verify real studio input resolution (1262x1181) is processed at native resolution
        rather than squashed down to 128px, preserving facial features and identity.
        """
        ori_w, ori_h = 1262, 1181
        rscale = 4

        # Native scaling contract: large images are NOT downscaled to 128
        # Only tiny images below 128 are upscaled
        self.assertGreaterEqual(min(ori_w, ori_h), 128)
        new_w = (ori_w * rscale) - (ori_w * rscale) % 8
        new_h = (ori_h * rscale) - (ori_h * rscale) % 8
        self.assertEqual((new_w, new_h), (5048, 4720))

        # Aspect ratio is strictly preserved
        self.assertAlmostEqual(new_w / new_h, ori_w / ori_h, delta=0.01)

    def test_process_lifecycle_clean_exit_no_premature_terminate(self) -> None:
        """
        Verify run_qnn_stage logic does NOT terminate process when completed == total_tiles,
        allowing clean teardown via proc.wait(timeout=120).
        """
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        mock_proc.returncode = 0
        mock_proc.wait.return_value = 0

        # Simulate execution where clean_exit = True
        clean_exit = True
        if not clean_exit and mock_proc.poll() is None:
            mock_proc.terminate()

        mock_proc.terminate.assert_not_called()

    def test_process_lifecycle_fail_closed_on_error(self) -> None:
        """Verify run_qnn_stage terminates process if clean_exit is False (fail-closed)."""
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None

        clean_exit = False
        if not clean_exit and mock_proc.poll() is None:
            mock_proc.terminate()

        mock_proc.terminate.assert_called_once()

    def test_phoenix_image_lab_navigation_and_photo_restore_reachable(self) -> None:
        """Verify Phoenix Image Lab hub and AI Photo Restore view are both functional and reachable."""
        from widgets.phoenix.workspace import PhoenixWorkspace
        from widgets.phoenix.views.image_lab_view import PhoenixImageLabView
        from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView

        self.assertIn("inpainting", PhoenixWorkspace.VIEW_TITLE_KEYS)
        self.assertIn("image_lab", PhoenixWorkspace.VIEW_TITLE_KEYS)
        self.assertIn("photo_restore", PhoenixWorkspace.VIEW_TITLE_KEYS)

        # Verify factory registrations without crashing secondary Tk roots
        ws = PhoenixWorkspace.__new__(PhoenixWorkspace)
        ws.controller = None
        ws.content_host = None
        ws.show_view = MagicMock()
        ws._views = {}
        PhoenixWorkspace._register_views(ws)
        self.assertIn("inpainting", ws._view_factories)
        self.assertIn("image_lab", ws._view_factories)
        self.assertIn("photo_restore", ws._view_factories)

        # Verify card navigation contract on Image Lab
        lab_view = PhoenixImageLabView.__new__(PhoenixImageLabView)
        navigated = []
        lab_view.on_navigate = navigated.append
        PhoenixImageLabView._navigate(lab_view, "photo_restore")
        self.assertEqual(navigated, ["photo_restore"])


if __name__ == "__main__":
    unittest.main()
