"""
HK NPU STUDIO - Phoenix Architecture
AI Photo Restore Focused Contract Tests

Comprehensive verification of all 14 Phase 1F architectural & runtime requirements:
1.  Grayscale detection (PIL L, 1, and RGB scan with channel diff < 3.0 vs color)
2.  DDColor skip on color image
3.  NAFNet always executed
4.  RealESRGAN 2x path
5.  RealESRGAN 4x path
6.  No CPU model fallback (enforces Qualcomm QNN HTP)
7.  Persistent runtime reuse (no reload between jobs)
8.  Clean close / release lifecycle
9.  Unique output filenames (color vs grayscale, collision avoidance)
10. Monotonic progress phase ordering (prepare -> restore -> colorize -> upscale -> save)
11. Cooperative cancellation between stages and before tiles
12. Structured error handling (all defined error codes)
13. Original image is never modified or overwritten
14. Proportional aspect ratio strictly preserved
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image

import config
from controllers.photo_restore_controller import PhotoRestoreController
from engine.backends.photo_restore_backend import (
    AIPhotoRestoreBackend,
    PhotoRestoreError,
    PhotoRestoreResult,
    is_grayscale_image,
    rgb2lab_np,
    lab2rgb_np,
    resolve_photo_restore_models,
    PHOTO_RESTORE_RUNTIME_UNAVAILABLE,
    PHOTO_RESTORE_NAFNET_MISSING,
    PHOTO_RESTORE_DDCOLOR_MISSING,
    PHOTO_RESTORE_QNN_HTP_UNAVAILABLE,
    PHOTO_RESTORE_INPUT_INVALID,
    PHOTO_RESTORE_NAFNET_FAILED,
    PHOTO_RESTORE_DDCOLOR_FAILED,
    PHOTO_RESTORE_UPSCALE_FAILED,
    PHOTO_RESTORE_CANCELLED,
    HISTORICAL_ACCURACY_DISCLAIMER,
)
from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView


class MockQNNContext:
    """Mock QNNContext for deterministic NPU contract testing."""

    def __init__(self, name: str, output_shape: tuple[int, ...] = (1, 1, 1, 1)) -> None:
        self.name = name
        self.output_shape = output_shape
        self.call_count = 0
        self.released = False

    def Inference(self, inputs: list[np.ndarray], **kwargs: Any) -> list[np.ndarray]:
        self.call_count += 1
        in_arr = inputs[0]
        if self.name == "nafnet_deblur":
            # Input: (1, 360, 640, 3) -> Output: (1, 360, 640, 3)
            return [in_arr.copy()]
        elif self.name == "ddcolor":
            # Input: (1, 256, 256, 3) -> Output: (1, 2, 256, 256)
            return [np.zeros((1, 2, 256, 256), dtype=np.float32)]
        elif self.name == "realesrgan":
            # Input: (1, 128, 128, 3) -> Output: (1, 512, 512, 3)
            # Produces 4x super-resolution tile
            return [np.repeat(np.repeat(in_arr, 4, axis=1), 4, axis=2)]
        return [np.zeros(self.output_shape, dtype=np.float32)]

    def release(self) -> None:
        self.released = True


class PhotoRestoreContractTests(unittest.TestCase):
    """Test suite verifying all 14 contracts for AI Photo Restore."""

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

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.out_dir = self.root / "output"
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # Create mock model files
        self.nafnet_file = self.root / "nafnet_deblur.dlc.bin"
        self.ddcolor_file = self.root / "ddcolor.dlc.bin"
        self.realesrgan_file = self.root / "real_esrgan_x4plus.bin"
        self.nafnet_file.write_bytes(b"MOCK_NAFNET")
        self.ddcolor_file.write_bytes(b"MOCK_DDCOLOR")
        self.realesrgan_file.write_bytes(b"MOCK_REALESRGAN")

        # Create test images
        # 1. Grayscale PIL L
        self.gray_l_path = self.root / "test_gray_l.png"
        Image.new("L", (100, 80), 128).save(self.gray_l_path)

        # 2. Grayscale RGB with near-identical channels
        self.gray_rgb_path = self.root / "test_gray_rgb.png"
        gray_arr = np.full((100, 80, 3), 128, dtype=np.uint8)
        # Add slight noise within threshold < 3.0
        gray_arr[..., 0] = 127
        gray_arr[..., 1] = 128
        gray_arr[..., 2] = 129
        Image.fromarray(gray_arr).save(self.gray_rgb_path)

        # 3. Vibrant Color RGB
        self.color_rgb_path = self.root / "test_color_rgb.png"
        color_arr = np.zeros((100, 80, 3), dtype=np.uint8)
        color_arr[:, :, 0] = 255  # High Red
        color_arr[:, :, 1] = 50   # Low Green
        color_arr[:, :, 2] = 20   # Low Blue
        Image.fromarray(color_arr).save(self.color_rgb_path)

        # Setup mock contexts and discovery
        self.ctx_nafnet = MockQNNContext("nafnet_deblur")
        self.ctx_ddcolor = MockQNNContext("ddcolor")
        self.ctx_realesrgan = MockQNNContext("realesrgan")

        self.mock_discovery = MagicMock()
        self.mock_discovery.qnn_htp_backend_path = str(self.root / "QnnHtp.dll")
        Path(self.mock_discovery.qnn_htp_backend_path).write_bytes(b"MOCK_DLL")

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def _create_backend(self) -> AIPhotoRestoreBackend:
        return AIPhotoRestoreBackend(
            nafnet_path=self.nafnet_file,
            ddcolor_path=self.ddcolor_file,
            realesrgan_path=self.realesrgan_file,
            discovery_service=self.mock_discovery,
            nafnet_context=self.ctx_nafnet,
            ddcolor_context=self.ctx_ddcolor,
            realesrgan_context=self.ctx_realesrgan,
        )

    # -----------------------------------------------------------------
    # Contract 1: Grayscale Detection
    # -----------------------------------------------------------------
    def test_01_grayscale_detection(self) -> None:
        """Verify robust grayscale detection on mode L, mode 1, and noisy RGB scans."""
        # 1. Single channel PIL modes
        img_l = Image.open(self.gray_l_path)
        self.assertTrue(is_grayscale_image(img_l))

        img_1 = Image.new("1", (50, 50), 1)
        self.assertTrue(is_grayscale_image(img_1))

        # 2. RGB image with near-identical channels (< 3.0 diff)
        img_gray_rgb = Image.open(self.gray_rgb_path)
        self.assertTrue(is_grayscale_image(img_gray_rgb))

        # 3. Vibrant color image (channel diff >> 3.0)
        img_color = Image.open(self.color_rgb_path)
        self.assertFalse(is_grayscale_image(img_color))

    # -----------------------------------------------------------------
    # Contract 2: DDColor Skip on Color Image
    # -----------------------------------------------------------------
    def test_02_ddcolor_skip_on_color_image(self) -> None:
        """Verify DDColor is skipped when the input photo is already color."""
        backend = self._create_backend()
        result = backend.restore(
            self.color_rgb_path,
            output_dir=self.out_dir,
            upscale_factor=4,
            auto_colorize=True,
        )
        self.assertTrue(result.success)
        self.assertFalse(result.is_colorized)
        self.assertEqual(result.metadata["colorization_model"], "skipped")
        self.assertEqual(self.ctx_ddcolor.call_count, 0)
        self.assertIn("_restored_x4.png", result.output_path)

    # -----------------------------------------------------------------
    # Contract 3: NAFNet Always Executed
    # -----------------------------------------------------------------
    def test_03_nafnet_always_used(self) -> None:
        """Verify NAFNet-DeBlur executes for both grayscale and color images."""
        backend = self._create_backend()

        # Job 1: Grayscale
        res_gray = backend.restore(self.gray_l_path, output_dir=self.out_dir)
        self.assertTrue(res_gray.success)
        count_after_gray = self.ctx_nafnet.call_count
        self.assertGreater(count_after_gray, 0)
        self.assertEqual(res_gray.metadata["restore_model"], "NAFNet-DeBlur")

        # Job 2: Color
        res_color = backend.restore(self.color_rgb_path, output_dir=self.out_dir)
        self.assertTrue(res_color.success)
        self.assertGreater(self.ctx_nafnet.call_count, count_after_gray)
        self.assertEqual(res_color.metadata["restore_model"], "NAFNet-DeBlur")

    # -----------------------------------------------------------------
    # Contract 4: RealESRGAN 2x Path
    # -----------------------------------------------------------------
    def test_04_realesrgan_2x_path(self) -> None:
        """Verify 2x upscale profile outputs exactly (width*2, height*2)."""
        backend = self._create_backend()
        in_img = Image.open(self.gray_l_path)
        orig_w, orig_h = in_img.size

        result = backend.restore(
            self.gray_l_path,
            output_dir=self.out_dir,
            upscale_factor=2,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.upscale_factor, 2)
        self.assertEqual(result.metadata["upscale_factor"], 2)

        out_img = Image.open(result.output_path)
        self.assertEqual(out_img.size, (orig_w * 2, orig_h * 2))

    # -----------------------------------------------------------------
    # Contract 5: RealESRGAN 4x Path
    # -----------------------------------------------------------------
    def test_05_realesrgan_4x_path(self) -> None:
        """Verify 4x upscale profile outputs exactly (width*4, height*4)."""
        backend = self._create_backend()
        in_img = Image.open(self.gray_l_path)
        orig_w, orig_h = in_img.size

        result = backend.restore(
            self.gray_l_path,
            output_dir=self.out_dir,
            upscale_factor=4,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.upscale_factor, 4)
        self.assertEqual(result.metadata["upscale_factor"], 4)

        out_img = Image.open(result.output_path)
        self.assertEqual(out_img.size, (orig_w * 4, orig_h * 4))

    # -----------------------------------------------------------------
    # Contract 6: No CPU Model Fallback (HTP Enforcement)
    # -----------------------------------------------------------------
    def test_06_no_cpu_fallback(self) -> None:
        """Verify backend fails closed if Qualcomm QNN HTP runtime is missing."""
        mock_discovery_missing_htp = MagicMock()
        mock_discovery_missing_htp.qnn_htp_backend_path = None

        backend = AIPhotoRestoreBackend(
            nafnet_path=self.nafnet_file,
            ddcolor_path=self.ddcolor_file,
            realesrgan_path=self.realesrgan_file,
            discovery_service=mock_discovery_missing_htp,
            nafnet_context=None,
            ddcolor_context=None,
            realesrgan_context=None,
        )

        with self.assertRaises(PhotoRestoreError) as ctx:
            backend.initialize()

        self.assertEqual(ctx.exception.code, PHOTO_RESTORE_QNN_HTP_UNAVAILABLE)
        self.assertIn("Snapdragon NPU", ctx.exception.message)

    # -----------------------------------------------------------------
    # Contract 7: Persistent Runtime Reuse
    # -----------------------------------------------------------------
    def test_07_persistent_runtime_reuse(self) -> None:
        """Verify runtime contexts remain resident across multiple sequential jobs."""
        backend = self._create_backend()
        self.assertEqual(backend.status, "INITIALIZED")

        # Job 1
        res1 = backend.restore(self.gray_l_path, output_dir=self.out_dir)
        self.assertTrue(res1.success)
        self.assertEqual(backend.status, "INITIALIZED")

        # Job 2
        res2 = backend.restore(self.gray_rgb_path, output_dir=self.out_dir)
        self.assertTrue(res2.success)
        self.assertEqual(backend.status, "INITIALIZED")

        # Verify same context objects handled both jobs without re-instantiation
        self.assertFalse(self.ctx_nafnet.released)
        self.assertFalse(self.ctx_ddcolor.released)
        self.assertFalse(self.ctx_realesrgan.released)

    # -----------------------------------------------------------------
    # Contract 8: Clean Close & Release Lifecycle
    # -----------------------------------------------------------------
    def test_08_close_release(self) -> None:
        """Verify close() releases context objects and prevents further jobs."""
        backend = self._create_backend()
        self.assertEqual(backend.status, "INITIALIZED")

        backend.close()
        self.assertEqual(backend.status, "CLOSED")
        self.assertTrue(self.ctx_nafnet.released)
        self.assertTrue(self.ctx_ddcolor.released)
        self.assertTrue(self.ctx_realesrgan.released)

        # Subsequent restore must fail with structured unavailable error
        res = backend.restore(self.gray_l_path, output_dir=self.out_dir)
        self.assertFalse(res.success)
        self.assertEqual(res.error_code, PHOTO_RESTORE_RUNTIME_UNAVAILABLE)

    # -----------------------------------------------------------------
    # Contract 9: Unique Output Filenames
    # -----------------------------------------------------------------
    def test_09_unique_output_filenames(self) -> None:
        """Verify unique filename generation and non-overwriting collision avoidance."""
        backend = self._create_backend()

        # Run 1: Grayscale -> produces _restored_color_x4.png
        res1 = backend.restore(self.gray_l_path, output_dir=self.out_dir, upscale_factor=4)
        self.assertTrue(res1.success)
        self.assertIn("test_gray_l_restored_color_x4.png", res1.output_path)

        # Run 2: Same input -> produces unique _001 suffix without collision
        res2 = backend.restore(self.gray_l_path, output_dir=self.out_dir, upscale_factor=4)
        self.assertTrue(res2.success)
        self.assertIn("test_gray_l_restored_color_x4_001.png", res2.output_path)
        self.assertTrue(Path(res1.output_path).exists())
        self.assertTrue(Path(res2.output_path).exists())
        self.assertNotEqual(res1.output_path, res2.output_path)

        # Run 3: Color image -> produces _restored_x4.png (no _color tag)
        res_col = backend.restore(self.color_rgb_path, output_dir=self.out_dir, upscale_factor=4)
        self.assertTrue(res_col.success)
        self.assertIn("test_color_rgb_restored_x4.png", res_col.output_path)
        self.assertNotIn("_restored_color_", res_col.output_path)

    # -----------------------------------------------------------------
    # Contract 10: Progress Phase Ordering
    # -----------------------------------------------------------------
    def test_10_progress_phase_order(self) -> None:
        """Verify callbacks follow prepare -> restore -> colorize -> upscale -> save."""
        backend = self._create_backend()
        events: list[tuple[str, float]] = []

        def progress(phase: str, pct: float, _detail: str | None) -> None:
            events.append((phase, pct))

        result = backend.restore(
            self.gray_l_path,
            output_dir=self.out_dir,
            progress_callback=progress,
        )
        self.assertTrue(result.success)

        # Check observed phases in order
        phases = [p for p, _ in events]
        distinct_phases: list[str] = []
        for p in phases:
            if not distinct_phases or distinct_phases[-1] != p:
                distinct_phases.append(p)

        self.assertEqual(
            distinct_phases,
            ["prepare", "restore", "colorize", "upscale", "save"],
        )

        # Check monotonically non-decreasing progress values
        pct_values = [pct for _, pct in events]
        for i in range(1, len(pct_values)):
            self.assertGreaterEqual(
                pct_values[i], pct_values[i - 1],
                f"Progress regression at event {i}: {pct_values[i]} < {pct_values[i-1]}",
            )
        self.assertEqual(pct_values[-1], 1.0)

    # -----------------------------------------------------------------
    # Contract 11: Cancel Between Stages
    # -----------------------------------------------------------------
    def test_11_cancel_between_stages(self) -> None:
        """Verify cooperative cancellation halts execution without publishing output."""
        backend = self._create_backend()

        def cancel_during_restore(phase: str, pct: float, _detail: str | None) -> None:
            if phase == "restore" and pct >= 0.08:
                backend.cancel()

        result = backend.restore(
            self.gray_l_path,
            output_dir=self.out_dir,
            progress_callback=cancel_during_restore,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error_code, PHOTO_RESTORE_CANCELLED)
        # Verify no file is published as output
        if result.output_path:
            self.assertFalse(Path(result.output_path).exists())

    # -----------------------------------------------------------------
    # Contract 12: Structured Error Codes
    # -----------------------------------------------------------------
    def test_12_structured_errors(self) -> None:
        """Verify structured error codes for all invalid parameter & environment states."""
        backend = self._create_backend()

        # 1. Invalid input file
        missing_file = self.root / "does_not_exist.jpg"
        res_missing = backend.restore(missing_file, output_dir=self.out_dir)
        self.assertFalse(res_missing.success)
        self.assertEqual(res_missing.error_code, PHOTO_RESTORE_INPUT_INVALID)

        # 2. Invalid upscale factor
        res_scale = backend.restore(self.gray_l_path, output_dir=self.out_dir, upscale_factor=8)
        self.assertFalse(res_scale.success)
        self.assertEqual(res_scale.error_code, PHOTO_RESTORE_INPUT_INVALID)

        # 3. Missing NAFNet file in initialize
        backend_no_naf = AIPhotoRestoreBackend(
            nafnet_path=self.root / "missing_nafnet.bin",
            ddcolor_path=self.ddcolor_file,
            realesrgan_path=self.realesrgan_file,
            discovery_service=self.mock_discovery,
        )
        with self.assertRaises(PhotoRestoreError) as ctx_naf:
            backend_no_naf.initialize()
        self.assertEqual(ctx_naf.exception.code, PHOTO_RESTORE_NAFNET_MISSING)

        # 4. Missing DDColor file in initialize
        backend_no_dd = AIPhotoRestoreBackend(
            nafnet_path=self.nafnet_file,
            ddcolor_path=self.root / "missing_ddcolor.bin",
            realesrgan_path=self.realesrgan_file,
            discovery_service=self.mock_discovery,
        )
        with self.assertRaises(PhotoRestoreError) as ctx_dd:
            backend_no_dd.initialize()
        self.assertEqual(ctx_dd.exception.code, PHOTO_RESTORE_DDCOLOR_MISSING)

        # 5. Missing RealESRGAN file in initialize
        backend_no_esr = AIPhotoRestoreBackend(
            nafnet_path=self.nafnet_file,
            ddcolor_path=self.ddcolor_file,
            realesrgan_path=self.root / "missing_realesrgan.bin",
            discovery_service=self.mock_discovery,
        )
        with self.assertRaises(PhotoRestoreError) as ctx_esr:
            backend_no_esr.initialize()
        self.assertEqual(ctx_esr.exception.code, PHOTO_RESTORE_UPSCALE_FAILED)

    # -----------------------------------------------------------------
    # Contract 13: Original Image Never Overwritten
    # -----------------------------------------------------------------
    def test_13_original_never_overwritten(self) -> None:
        """Verify original file content, hash, and metadata remain untouched."""
        backend = self._create_backend()
        orig_bytes = self.gray_l_path.read_bytes()
        orig_hash = hashlib.sha256(orig_bytes).hexdigest()
        orig_mtime = self.gray_l_path.stat().st_mtime

        result = backend.restore(self.gray_l_path, output_dir=self.out_dir)
        self.assertTrue(result.success)

        # Verify original file
        post_bytes = self.gray_l_path.read_bytes()
        post_hash = hashlib.sha256(post_bytes).hexdigest()
        post_mtime = self.gray_l_path.stat().st_mtime

        self.assertEqual(orig_hash, post_hash)
        self.assertEqual(orig_bytes, post_bytes)
        self.assertEqual(orig_mtime, post_mtime)
        self.assertNotEqual(Path(result.output_path).resolve(), self.gray_l_path.resolve())

    # -----------------------------------------------------------------
    # Contract 14: Aspect Ratio Strictly Preserved
    # -----------------------------------------------------------------
    def test_14_aspect_ratio_preserved(self) -> None:
        """Verify aspect ratio is strictly preserved across both 2x and 4x upscaling."""
        backend = self._create_backend()

        # Test non-square dimensions: 130 x 75
        non_square_path = self.root / "non_square.png"
        Image.new("RGB", (130, 75), (50, 50, 50)).save(non_square_path)
        orig_ratio = 130 / 75

        # Factor 2x
        res_2x = backend.restore(non_square_path, output_dir=self.out_dir, upscale_factor=2)
        self.assertTrue(res_2x.success)
        out_2x = Image.open(res_2x.output_path)
        self.assertEqual(out_2x.size, (260, 150))
        self.assertAlmostEqual(out_2x.width / out_2x.height, orig_ratio, places=4)

        # Factor 4x
        res_4x = backend.restore(non_square_path, output_dir=self.out_dir, upscale_factor=4)
        self.assertTrue(res_4x.success)
        out_4x = Image.open(res_4x.output_path)
        self.assertEqual(out_4x.size, (520, 300))
        self.assertAlmostEqual(out_4x.width / out_4x.height, orig_ratio, places=4)

        # Sidecar JSON check
        sidecar_path = Path(res_4x.output_path).with_suffix(".json")
        self.assertTrue(sidecar_path.is_file())
        sidecar_data = json.loads(sidecar_path.read_text(encoding="utf-8"))
        self.assertTrue(sidecar_data["aspect_ratio_preserved"])
        self.assertEqual(sidecar_data["input_size"], [130, 75])
        self.assertEqual(sidecar_data["output_size"], [520, 300])
        self.assertEqual(sidecar_data["disclaimer"], HISTORICAL_ACCURACY_DISCLAIMER)

    # -----------------------------------------------------------------
    # Additional Integration: Controller Threading & Callback Boundary
    # -----------------------------------------------------------------
    def test_controller_threading_and_ui_dispatch(self) -> None:
        """Verify PhotoRestoreController coordinates background execution and ui_dispatch."""
        backend = self._create_backend()
        dispatched_events: list[Any] = []

        def custom_ui_dispatch(callback: Any) -> None:
            dispatched_events.append("dispatched")
            callback()

        controller = PhotoRestoreController(
            backend=backend,
            ui_dispatch=custom_ui_dispatch,
        )

        completed_results: list[PhotoRestoreResult] = []
        progress_calls: list[tuple[str, float, str | None]] = []

        controller.start(
            image_path=self.gray_l_path,
            output_dir=self.out_dir,
            upscale_factor=4,
            auto_colorize=True,
            on_progress=lambda phase, val, det: progress_calls.append((phase, val, det)),
            on_complete=completed_results.append,
            asynchronous=False,
        )

        self.assertEqual(len(completed_results), 1)
        self.assertTrue(completed_results[0].success)
        self.assertGreater(len(progress_calls), 0)
        self.assertGreater(len(dispatched_events), 0)

    # -----------------------------------------------------------------
    # Contract 15: Real Color Sample Skip Contract
    # -----------------------------------------------------------------
    def test_15_color_image_fixture_contract(self) -> None:
        """Verify the portable color fixture is recognized as color and skips DDColor."""
        with Image.open(self.color_rgb_path) as img:
            is_gray = is_grayscale_image(img)
        self.assertFalse(is_gray)

        backend = self._create_backend()
        result = backend.restore(
            self.color_rgb_path,
            output_dir=self.out_dir,
            auto_colorize=True,
        )
        self.assertTrue(result.success)
        self.assertFalse(result.is_colorized)
        self.assertEqual(result.metadata["colorization_model"], "skipped")
        self.assertEqual(self.ctx_ddcolor.call_count, 0)

    # -----------------------------------------------------------------
    # Contract 16: Thread-Safe Queue Dispatch & Main-Thread Execution
    # -----------------------------------------------------------------
    def test_16_worker_ui_dispatch_executes_on_main_thread_after_pump(self) -> None:
        """Worker thread dispatches callback to view queue; runs in main thread on pump."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            main_tid = threading.get_ident()
            recorded_tid: list[int] = []
            delivered_payload: list[str] = []
            worker_tid: list[int] = []

            def worker() -> None:
                worker_tid.append(threading.get_ident())
                view.ui_dispatch(lambda: (
                    recorded_tid.append(threading.get_ident()),
                    delivered_payload.append("success"),
                ))

            t = threading.Thread(target=worker, name="test-worker")
            t.start()
            t.join()

            # Before pump: callback has NOT run yet
            self.assertEqual(len(delivered_payload), 0)
            self.assertFalse(view._ui_dispatch_queue.empty())

            # Now pump from main thread
            view._drain_ui_dispatch_queue()

            # After pump: callback ran in main thread, NOT worker thread
            self.assertEqual(delivered_payload, ["success"])
            self.assertEqual(recorded_tid[0], main_tid)
            self.assertNotEqual(recorded_tid[0], worker_tid[0])
            self.assertTrue(view._ui_dispatch_queue.empty())
        finally:
            view.destroy()

    # -----------------------------------------------------------------
    # Contract 17: Worker Progress Callback via Queue Pump
    # -----------------------------------------------------------------
    def test_17_worker_progress_callback_delivered_via_queue_pump(self) -> None:
        """Progress updates from background worker are queued and pumped to main thread."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            backend = self._create_backend()
            controller = PhotoRestoreController(
                backend=backend,
                ui_dispatch=view.ui_dispatch,
            )
            progress_events: list[tuple[str, float, str | None]] = []

            controller.start(
                image_path=self.gray_l_path,
                output_dir=self.out_dir,
                upscale_factor=4,
                auto_colorize=True,
                on_progress=lambda phase, val, det: progress_events.append((phase, val, det)),
                asynchronous=True,
            )

            deadline = time.monotonic() + 5.0
            while controller.running and time.monotonic() < deadline:
                view._drain_ui_dispatch_queue()
                time.sleep(0.01)
            view._drain_ui_dispatch_queue()

            self.assertFalse(controller.running)
            self.assertGreater(len(progress_events), 0)
            self.assertEqual(progress_events[0][0], "prepare")
        finally:
            view.destroy()

    # -----------------------------------------------------------------
    # Contract 18: Worker Completion Callback via Queue Pump
    # -----------------------------------------------------------------
    def test_18_worker_completion_callback_delivered_via_queue_pump(self) -> None:
        """Completion result from background worker is delivered via queue pump."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            backend = self._create_backend()
            controller = PhotoRestoreController(
                backend=backend,
                ui_dispatch=view.ui_dispatch,
            )
            results: list[PhotoRestoreResult] = []

            controller.start(
                image_path=self.gray_l_path,
                output_dir=self.out_dir,
                upscale_factor=4,
                auto_colorize=True,
                on_complete=results.append,
                asynchronous=True,
            )

            deadline = time.monotonic() + 5.0
            while controller.running and time.monotonic() < deadline:
                view._drain_ui_dispatch_queue()
                time.sleep(0.01)
            view._drain_ui_dispatch_queue()

            self.assertFalse(controller.running)
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].success)
        finally:
            view.destroy()

    # -----------------------------------------------------------------
    # Contract 19: Worker Exception Delivers Failure Without Starvation
    # -----------------------------------------------------------------
    def test_19_worker_exception_delivers_failure_and_does_not_starve(self) -> None:
        """Worker encountering backend exception delivers failure result via ui_dispatch."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            backend = self._create_backend()
            backend.restore = MagicMock(side_effect=RuntimeError("Simulated backend crash"))
            controller = PhotoRestoreController(
                backend=backend,
                ui_dispatch=view.ui_dispatch,
            )
            results: list[PhotoRestoreResult] = []

            controller.start(
                image_path=self.gray_l_path,
                output_dir=self.out_dir,
                upscale_factor=4,
                auto_colorize=True,
                on_complete=results.append,
                asynchronous=True,
            )

            deadline = time.monotonic() + 5.0
            while controller.running and time.monotonic() < deadline:
                view._drain_ui_dispatch_queue()
                time.sleep(0.01)
            view._drain_ui_dispatch_queue()

            self.assertFalse(controller.running)
            self.assertEqual(len(results), 1)
            self.assertFalse(results[0].success)
            self.assertIn("Simulated backend crash", results[0].error_message or "")
        finally:
            view.destroy()

    # -----------------------------------------------------------------
    # Contract 20: Destroy Stops Dispatcher Cleanly
    # -----------------------------------------------------------------
    def test_20_destroy_stops_dispatcher_cleanly(self) -> None:
        """Destroying the view cancels pump, closes dispatch, and rejects future calls."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        self.assertFalse(view._ui_dispatch_closed)
        self.assertIsNotNone(view._ui_pump_id)

        view.destroy()

        self.assertTrue(view._ui_dispatch_closed)
        self.assertIsNone(view._ui_pump_id)

        called: list[bool] = []
        view.ui_dispatch(lambda: called.append(True))
        self.assertTrue(view._ui_dispatch_queue.empty())
        self.assertEqual(len(called), 0)

    # -----------------------------------------------------------------
    # Contract 21: Zero Direct Tk After Calls from Worker Thread
    # -----------------------------------------------------------------
    def test_21_no_direct_tk_after_calls_from_worker(self) -> None:
        """Assert that PhoenixPhotoRestoreView.ui_dispatch makes zero widget.after calls."""
        view = PhoenixPhotoRestoreView(self.tk_root)
        try:
            with patch.object(view, "after") as mock_after:
                worker_errors: list[Exception] = []

                def worker() -> None:
                    try:
                        view.ui_dispatch(lambda: None)
                    except Exception as e:
                        worker_errors.append(e)

                t = threading.Thread(target=worker, name="tk-safety-worker")
                t.start()
                t.join()

                self.assertEqual(len(worker_errors), 0)
                self.assertEqual(mock_after.call_count, 0)
                self.assertEqual(view._ui_dispatch_queue.qsize(), 1)
        finally:
            view.destroy()

    # -----------------------------------------------------------------
    # Contract 22: Controller Running Cleared Reliably on Exception
    # -----------------------------------------------------------------
    def test_22_controller_running_cleared_reliably_on_exception(self) -> None:
        """Controller.running returns False immediately after worker completes or fails."""
        backend = self._create_backend()
        backend.restore = MagicMock(side_effect=ValueError("Simulated worker failure"))
        controller = PhotoRestoreController(backend=backend)

        results: list[PhotoRestoreResult] = []
        controller.start(
            image_path=self.gray_l_path,
            on_complete=results.append,
            asynchronous=True,
        )

        deadline = time.monotonic() + 5.0
        while controller.running and time.monotonic() < deadline:
            time.sleep(0.01)

        self.assertFalse(controller.running)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)

    # -----------------------------------------------------------------
    # Contract 23: Backend RLock Prevents Re-entrant Deadlock on Restore
    # -----------------------------------------------------------------
    def test_23_backend_rlock_prevents_reentrant_deadlock(self) -> None:
        """Verify that restore() calling initialize() while holding lock does not deadlock."""
        backend = AIPhotoRestoreBackend(
            nafnet_path=self.nafnet_file,
            ddcolor_path=self.ddcolor_file,
            realesrgan_path=self.realesrgan_file,
            discovery_service=self.mock_discovery,
        )
        self.assertEqual(backend.status, "UNINITIALIZED")
        self.assertIsInstance(backend._lock, type(threading.RLock()))

        # Mock initialize to attach mock contexts
        def fake_initialize() -> None:
            with backend._lock:
                backend.ctx_nafnet = self.ctx_nafnet
                backend.ctx_ddcolor = self.ctx_ddcolor
                backend.ctx_realesrgan = self.ctx_realesrgan
                backend._status = "INITIALIZED"

        backend.initialize = fake_initialize

        # Must execute cleanly without deadlocking
        result = backend.restore(
            image_path=self.gray_l_path,
            output_dir=self.out_dir,
            upscale_factor=4,
        )
        self.assertTrue(result.success)
        self.assertEqual(backend.status, "INITIALIZED")
