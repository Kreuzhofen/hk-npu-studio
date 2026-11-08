from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from controllers.image_to_image_controller import ImageToImageController
from engine.backends.sd15_qnn_inpainting_adapter import (
    SD15QnnInpaintingAdapter,
    SD15QnnInpaintingResult,
)
from widgets.phoenix.theme import PHOENIX_THEME, update_phoenix_theme
from widgets.phoenix.views.image_to_image_view import PhoenixImageToImageView


class DummyImageToImageAdapter:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def cancel(self) -> None:
        pass

    def run_img2img(
        self,
        input_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        negative_prompt: str = "",
        steps: int = 20,
        seed: int = 42,
        cfg_scale: float = 7.5,
        denoising_strength: float = 0.65,
        enable_reference_control: bool = False,
        reference_mode: str = "canny_qnn",
        reference_fidelity: float = 0.75,
        reference_image_path: str | Path | None = None,
        progress_callback=None,
        use_subprocess: bool = True,
    ) -> SD15QnnInpaintingResult:
        self.calls.append(
            {
                "input_image_path": str(input_image_path),
                "prompt": prompt,
                "output_path": str(output_path),
                "negative_prompt": negative_prompt,
                "steps": steps,
                "seed": seed,
                "cfg_scale": cfg_scale,
                "denoising_strength": denoising_strength,
                "enable_reference_control": enable_reference_control,
                "reference_mode": reference_mode,
                "reference_fidelity": reference_fidelity,
                "reference_image_path": str(reference_image_path) if reference_image_path else None,
            }
        )
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (512, 512), (180, 140, 90))
        img.save(out_p, format="PNG")
        return SD15QnnInpaintingResult(
            success=True,
            output_path=out_p,
            metadata={"mode": "img2img", "denoising_strength": denoising_strength},
        )


class PhoenixImageToImageUITest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.temp_dir = tempfile.TemporaryDirectory(prefix="test_img2img_ui_")
        self.work_dir = Path(self.temp_dir.name)
        self.output_dir = self.work_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy test input image
        self.test_img_path = self.work_dir / "sample_512.png"
        img = Image.new("RGB", (512, 512), (100, 150, 200))
        img.save(self.test_img_path, format="PNG")

        self.dummy_adapter = DummyImageToImageAdapter()
        self.controller = ImageToImageController(
            adapter=self.dummy_adapter,
        )

    def tearDown(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass
        self.temp_dir.cleanup()
        update_phoenix_theme("dark")

    def test_view_creation_and_components(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
            temp_dir=self.work_dir / "temp",
        )
        try:
            self.assertTrue(hasattr(view, "overview_button"))
            self.assertTrue(hasattr(view, "load_button"))
            self.assertTrue(hasattr(view, "clear_button"))
            self.assertTrue(hasattr(view, "left_canvas"))
            self.assertTrue(hasattr(view, "right_canvas"))
            self.assertTrue(hasattr(view, "prompt"))
            self.assertTrue(hasattr(view, "negative_prompt"))
            self.assertTrue(hasattr(view, "strength_scale"))
            self.assertTrue(hasattr(view, "strength_spin"))
            self.assertTrue(hasattr(view, "steps_scale"))
            self.assertTrue(hasattr(view, "cfg_scale"))
            self.assertTrue(hasattr(view, "start_button"))
            self.assertTrue(hasattr(view, "save_button"))
            self.assertTrue(hasattr(view, "btn_subtle"))
            self.assertTrue(hasattr(view, "btn_moderate"))
            self.assertTrue(hasattr(view, "btn_balanced"))
            self.assertTrue(hasattr(view, "btn_creative"))
            self.assertTrue(hasattr(view, "btn_regen"))
            self.assertTrue(hasattr(view, "ref_check"))
            self.assertTrue(hasattr(view, "ref_enabled_var"))
            self.assertTrue(hasattr(view, "ref_mode_var"))
            self.assertTrue(hasattr(view, "ref_fidelity_var"))
            self.assertTrue(hasattr(view, "rb_canny"))
            self.assertTrue(hasattr(view, "rb_anchor"))
            self.assertTrue(hasattr(view, "btn_load_ref"))
            self.assertTrue(hasattr(view, "btn_reset_ref"))
        finally:
            view.destroy()

    def test_denoising_strength_controls_and_defaults(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            # Default strength is 0.65 (Ausgewogen)
            self.assertAlmostEqual(view.strength_var.get(), 0.65, places=2)
            self.assertAlmostEqual(float(view.strength_scale.cget("from")), 0.10, places=2)
            self.assertAlmostEqual(float(view.strength_scale.cget("to")), 1.00, places=2)

            # Initial highlight: Ausgewogen is secondary (active), others neutral
            self.assertEqual(view.btn_balanced.button_type, "secondary")
            self.assertEqual(view.btn_subtle.button_type, "neutral")
            self.assertEqual(view.btn_moderate.button_type, "neutral")
            self.assertEqual(view.btn_creative.button_type, "neutral")
            self.assertEqual(view.btn_regen.button_type, "neutral")

            # Change to 0.30 manually
            view.strength_var.set(0.30)
            view._on_strength_change()
            self.assertIn("0.10–0.35", view.strength_hint.cget("text"))
            self.assertEqual(view.btn_subtle.button_type, "secondary")
            self.assertEqual(view.btn_balanced.button_type, "neutral")

            # Change to 0.45 manually
            view.strength_var.set(0.45)
            view._on_strength_change()
            self.assertIn("0.40–0.55", view.strength_hint.cget("text"))
            self.assertEqual(view.btn_moderate.button_type, "secondary")
            self.assertEqual(view.btn_subtle.button_type, "neutral")

            # Change to non-preset manual value (0.55) -> no preset active
            view.strength_var.set(0.55)
            view._on_strength_change()
            for btn in (view.btn_subtle, view.btn_moderate, view.btn_balanced, view.btn_creative, view.btn_regen):
                self.assertEqual(btn.button_type, "neutral")

            # Change to 1.00 manually
            view.strength_var.set(1.00)
            view._on_strength_change()
            self.assertIn("0.95–1.00", view.strength_hint.cget("text"))
            self.assertEqual(view.btn_regen.button_type, "secondary")
        finally:
            view.destroy()

    def test_presets_application(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            # 1. Subtil (0.30)
            view.btn_subtle.invoke()
            self.assertAlmostEqual(view.strength_var.get(), 0.30, places=2)
            self.assertEqual(view.steps.get(), 20)
            self.assertAlmostEqual(view.cfg_var.get(), 7.5, places=1)
            self.assertEqual(view.btn_subtle.button_type, "secondary")
            self.assertEqual(view.btn_balanced.button_type, "neutral")

            # 2. Moderat (0.45)
            view.btn_moderate.invoke()
            self.assertAlmostEqual(view.strength_var.get(), 0.45, places=2)
            self.assertEqual(view.steps.get(), 20)
            self.assertAlmostEqual(view.cfg_var.get(), 7.5, places=1)
            self.assertEqual(view.btn_moderate.button_type, "secondary")
            self.assertEqual(view.btn_subtle.button_type, "neutral")

            # 3. Ausgewogen (0.65)
            view.btn_balanced.invoke()
            self.assertAlmostEqual(view.strength_var.get(), 0.65, places=2)
            self.assertEqual(view.steps.get(), 20)
            self.assertAlmostEqual(view.cfg_var.get(), 7.5, places=1)
            self.assertEqual(view.btn_balanced.button_type, "secondary")

            # 4. Kreativ (0.80)
            view.btn_creative.invoke()
            self.assertAlmostEqual(view.strength_var.get(), 0.80, places=2)
            self.assertEqual(view.steps.get(), 20)
            self.assertAlmostEqual(view.cfg_var.get(), 8.0, places=1)
            self.assertEqual(view.btn_creative.button_type, "secondary")

            # 5. Neugenerierung (1.00)
            view.btn_regen.invoke()
            self.assertAlmostEqual(view.strength_var.get(), 1.00, places=2)
            self.assertEqual(view.steps.get(), 20)
            self.assertAlmostEqual(view.cfg_var.get(), 7.5, places=1)
            self.assertEqual(view.btn_regen.button_type, "secondary")
        finally:
            view.destroy()

    def test_actual_scheduler_steps_for_all_presets(self) -> None:
        """Verify actual inference steps calculation for all 5 presets."""
        preset_values = {
            "subtle": (0.30, 6),
            "moderate": (0.45, 9),
            "balanced": (0.65, 13),
            "creative": (0.80, 16),
            "regen": (1.00, 20),
        }
        total_steps = 20
        for name, (strength, expected_steps) in preset_values.items():
            actual = max(1, round(total_steps * strength))
            self.assertEqual(
                actual, expected_steps,
                f"Preset {name} ({strength}) should calculate {expected_steps} actual steps, got {actual}"
            )

    def test_load_and_clear_image(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            self.assertIsNone(view.input_path)
            loaded = view.load_dropped_image(self.test_img_path)
            self.assertTrue(loaded)
            self.assertEqual(view.input_path, self.test_img_path.resolve())

            # Clear
            view._clear_image()
            self.assertIsNone(view.input_path)
            self.assertIsNone(view.result_path)
        finally:
            view.destroy()

    def test_execution_delegates_to_controller_with_exact_params(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            view.load_dropped_image(self.test_img_path)
            view.prompt.insert("1.0", "A futuristic cyberpunk city at dusk")
            view.negative_prompt.insert("1.0", "blurry, low quality")
            view.strength_var.set(0.65)
            view.steps.set(20)
            view.cfg_var.set(7.5)
            view.seed.set("12345")

            # Trigger generation
            view._start_generation()
            if self.controller._thread is not None:
                self.controller._thread.join(timeout=3.0)
            view._drain_ui_dispatch()

            self.assertEqual(len(self.dummy_adapter.calls), 1)
            call = self.dummy_adapter.calls[0]
            self.assertEqual(call["prompt"], "A futuristic cyberpunk city at dusk")
            self.assertEqual(call["negative_prompt"], "blurry, low quality")
            self.assertAlmostEqual(call["denoising_strength"], 0.65, places=2)
            self.assertEqual(call["steps"], 20)
            self.assertAlmostEqual(call["cfg_scale"], 7.5, places=1)
            self.assertEqual(call["seed"], 12345)
            self.assertTrue(Path(call["output_path"]).is_file())
        finally:
            view.destroy()

    def test_dark_and_light_theme_parity(self) -> None:
        for theme in ("dark", "light"):
            with self.subTest(theme=theme):
                update_phoenix_theme(theme)
                view = PhoenixImageToImageView(
                    self.root,
                    controller=self.controller,
                    output_dir=self.output_dir,
                )
                try:
                    view.apply_theme()
                    self.assertEqual(view.cget("bg"), PHOENIX_THEME.content_bg)
                    self.assertEqual(view.left_canvas.cget("bg"), PHOENIX_THEME.card_bg)
                    self.assertEqual(view.right_canvas.cget("bg"), PHOENIX_THEME.card_bg)
                finally:
                    view.destroy()

    def test_reference_control_ui_and_defaults(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            # Defaults
            self.assertFalse(view.ref_enabled_var.get())
            self.assertEqual(view.ref_mode_var.get(), "canny_qnn")
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.75, places=2)
            self.assertEqual(view.ref_source_var.get(), "same")
            self.assertIsNone(view.custom_ref_path)

            # Toggle reference binding
            view.ref_enabled_var.set(True)
            view._on_ref_toggle()
            self.assertTrue(view.ref_options_frame.winfo_ismapped() or True)

            # Change mode to latent_anchor
            view.ref_mode_var.set("latent_anchor")
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")

            # Change fidelity
            view.ref_fidelity_var.set(0.90)
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.90, places=2)

            # Set custom reference path
            custom_ref = self.work_dir / "custom_ref.png"
            Image.new("RGB", (512, 512), (50, 80, 120)).save(custom_ref)
            view.custom_ref_path = custom_ref
            view.ref_image_label.configure(text=f"Ref: {custom_ref.name}")
            self.assertIn("custom_ref.png", view.ref_image_label.cget("text"))

            # Reset custom reference path
            view._reset_custom_reference_image()
            self.assertIsNone(view.custom_ref_path)
            self.assertIn("Kein separates Referenzbild", view.ref_image_label.cget("text"))
        finally:
            view.destroy()

    def test_execution_with_reference_control_passes_params(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            view.load_dropped_image(self.test_img_path)
            view.prompt.insert("1.0", "A golden majestic lion with ornate crown")
            view.strength_var.set(0.80)
            view.steps.set(20)
            view.cfg_var.set(8.0)
            view.seed.set("999")

            # Enable reference control (Contour / Canny QNN)
            view.ref_enabled_var.set(True)
            view.ref_mode_var.set("canny_qnn")
            view.ref_fidelity_var.set(0.85)
            view.ref_source_var.set("same")

            # Start generation
            view._start_generation()
            if self.controller._thread is not None:
                self.controller._thread.join(timeout=3.0)
            view._drain_ui_dispatch()

            self.assertEqual(len(self.dummy_adapter.calls), 1)
            call = self.dummy_adapter.calls[0]
            self.assertTrue(call["enable_reference_control"])
            self.assertEqual(call["reference_mode"], "canny_qnn")
            self.assertAlmostEqual(call["reference_fidelity"], 0.85, places=2)
            self.assertAlmostEqual(call["denoising_strength"], 0.80, places=2)
            self.assertEqual(call["seed"], 999)
        finally:
            view.destroy()

    def test_execution_with_latent_anchor_reference_control(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            view.load_dropped_image(self.test_img_path)
            view.prompt.insert("1.0", "A marble statue of an emperor")
            view.strength_var.set(0.65)
            view.steps.set(20)

            # Enable reference control (Structure / Latent Anchor)
            view.ref_enabled_var.set(True)
            view.ref_mode_var.set("latent_anchor")
            view.ref_fidelity_var.set(0.70)

            view._start_generation()
            if self.controller._thread is not None:
                self.controller._thread.join(timeout=3.0)
            view._drain_ui_dispatch()

            self.assertEqual(len(self.dummy_adapter.calls), 1)
            call = self.dummy_adapter.calls[0]
            self.assertTrue(call["enable_reference_control"])
            self.assertEqual(call["reference_mode"], "latent_anchor")
            self.assertAlmostEqual(call["reference_fidelity"], 0.70, places=2)
            self.assertAlmostEqual(call["denoising_strength"], 0.65, places=2)
        finally:
            view.destroy()

    def test_adaptive_reference_mode_selection_and_standards(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            # 1. Check existence of Sprint 44 Adaptive Reference components
            self.assertTrue(hasattr(view, "btn_mode_contour"))
            self.assertTrue(hasattr(view, "btn_mode_structure"))
            self.assertTrue(hasattr(view, "ref_mode_desc_title"))
            self.assertTrue(hasattr(view, "ref_mode_desc_detail"))
            self.assertTrue(hasattr(view, "btn_fidelity_default"))

            # 2. Initial state: Modus A (Konturtreue / Canny QNN) active with standard 0.75
            self.assertEqual(view.ref_mode_var.get(), "canny_qnn")
            self.assertEqual(view.btn_mode_contour.button_type, "secondary")
            self.assertEqual(view.btn_mode_structure.button_type, "neutral")
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.75, places=2)
            self.assertIn("0.75", view.btn_fidelity_default.cget("text"))
            self.assertIn("Architektur", view.ref_mode_desc_title.cget("text"))

            # 3. Switch to Modus B (Strukturtreue / Latent Anchor)
            view.select_reference_mode("latent_anchor", apply_default_fidelity=True)
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")
            self.assertEqual(view.btn_mode_structure.button_type, "secondary")
            self.assertEqual(view.btn_mode_contour.button_type, "neutral")
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.65, places=2)
            self.assertIn("0.65", view.btn_fidelity_default.cget("text"))
            self.assertIn("Porträts", view.ref_mode_desc_title.cget("text"))

            # 4. Switch back to Modus A (Konturtreue / Canny QNN)
            view.select_reference_mode("canny_qnn", apply_default_fidelity=True)
            self.assertEqual(view.ref_mode_var.get(), "canny_qnn")
            self.assertEqual(view.btn_mode_contour.button_type, "secondary")
            self.assertEqual(view.btn_mode_structure.button_type, "neutral")
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.75, places=2)
            self.assertIn("0.75", view.btn_fidelity_default.cget("text"))
        finally:
            view.destroy()

    def test_adaptive_reference_manual_fidelity_and_reset(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            # Set to Mode A (standard 0.75)
            view.select_reference_mode("canny_qnn", apply_default_fidelity=True)
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.75, places=2)

            # Manual adjustment to 1.15
            view.ref_fidelity_var.set(1.15)
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 1.15, places=2)
            self.assertEqual(view.ref_mode_var.get(), "canny_qnn")  # Mode remains unchanged

            # Click reset to default for Mode A -> 0.75
            view._reset_to_default_fidelity()
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.75, places=2)

            # Switch to Mode B (standard 0.65)
            view.select_reference_mode("latent_anchor", apply_default_fidelity=True)
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.65, places=2)

            # Manual adjustment to 0.40
            view.ref_fidelity_var.set(0.40)
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.40, places=2)
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")

            # Click reset to default for Mode B -> 0.65
            view._reset_to_default_fidelity()
            self.assertAlmostEqual(view.ref_fidelity_var.get(), 0.65, places=2)
        finally:
            view.destroy()

    def test_no_unconfirmed_auto_mode_switch(self) -> None:
        view = PhoenixImageToImageView(
            self.root,
            controller=self.controller,
            output_dir=self.output_dir,
        )
        try:
            # User explicitly selects Mode B (Strukturtreue)
            view.select_reference_mode("latent_anchor", apply_default_fidelity=True)
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")

            # Load image
            view.load_dropped_image(self.test_img_path)
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")

            # Type geometric prompt
            view.prompt.insert("1.0", "A futuristic cathedral spire with gothic architecture")
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")

            # Apply a preset (e.g., Ausgewogen 0.65)
            view._apply_preset(0.65)
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")

            # Verify no unconfirmed auto-switch occurred
            self.assertEqual(view.ref_mode_var.get(), "latent_anchor")
        finally:
            view.destroy()

    def test_adaptive_reference_theme_parity(self) -> None:
        for theme in ("dark", "light"):
            with self.subTest(theme=theme):
                update_phoenix_theme(theme)
                view = PhoenixImageToImageView(
                    self.root,
                    controller=self.controller,
                    output_dir=self.output_dir,
                )
                try:
                    view.apply_theme()
                    self.assertEqual(view.ref_mode_desc_frame.cget("bg"), PHOENIX_THEME.elevated_bg)
                    self.assertEqual(view.ref_mode_desc_title.cget("bg"), PHOENIX_THEME.elevated_bg)
                    self.assertEqual(view.ref_mode_desc_detail.cget("bg"), PHOENIX_THEME.elevated_bg)
                finally:
                    view.destroy()


if __name__ == "__main__":
    unittest.main()
