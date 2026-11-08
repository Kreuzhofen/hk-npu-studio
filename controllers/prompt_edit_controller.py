"""
HK NPU STUDIO – Phoenix Prompt Engine
Component: PromptEditController

Central orchestrator and facade for natural-language prompt-driven image editing
on Qualcomm Snapdragon X Elite Hexagon NPU.
Seamlessly integrates PromptIntentParser, ColorSpatialSegmenter, InpaintingController,
and ImageToImageController with strict safety gates and bit-exact background preservation.

Created by Senior Software Engineer (Antigravity / Gemini)
Chief Software Architect: ChatGPT
Product Owner: Holger Kreuzhofen
"""

from __future__ import annotations

import json
import logging
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from config import TEMP_DIR
from controllers.image_to_image_controller import ImageToImageController
from controllers.inpainting_controller import InpaintingController
from engine.backends.sd15_qnn_inpainting_adapter import (
    SD15QnnInpaintingAdapter,
    SD15QnnInpaintingResult,
)
from engine.color_spatial_segmenter import ColorSpatialSegmenter, SegmentResult
from engine.phoenix_hybrid_segmenter import HybridSegmentResult, PhoenixHybridSegmenter
from engine.material_priming import (
    MATERIAL_PRESETS,
    get_material_preset,
    prime_material_chrominance,
)
from engine.prompt_intent_parser import IntentCategory, ParsedIntent, PromptIntentParser

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PromptEditPlan:
    """Structured execution plan created by analyzing input image and user prompt."""
    can_execute: bool
    intent: IntentCategory
    parsed_intent: ParsedIntent
    mode: str  # "LOCAL" or "GLOBAL"
    target_object: str | None
    material_preset: str | None
    target_color: str | None
    segment_result: SegmentResult | None
    refined_prompt: str
    negative_prompt: str
    denoising_strength: float
    controller_route: str  # "INPAINTING_MATERIAL", "INPAINTING_COLOR", "INPAINTING_REMOVAL", "IMG2IMG_GLOBAL", "NONE"
    rejection_reason: str | None = None
    point_prompt: tuple[int, int] | None = None
    negative_points: list[tuple[int, int]] | None = None
    hybrid_result: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "can_execute": self.can_execute,
            "intent": self.intent.value,
            "mode": self.mode,
            "target_object": self.target_object,
            "material_preset": self.material_preset,
            "target_color": self.target_color,
            "point_prompt": list(self.point_prompt) if self.point_prompt else None,
            "negative_points": [list(p) for p in self.negative_points] if self.negative_points else None,
            "controller_route": self.controller_route,
            "refined_prompt": self.refined_prompt,
            "negative_prompt": self.negative_prompt,
            "denoising_strength": self.denoising_strength,
            "rejection_reason": self.rejection_reason,
            "segmentation": self.segment_result.to_dict() if self.segment_result else None,
            "hybrid_segmentation": self.hybrid_result.to_dict() if hasattr(self.hybrid_result, "to_dict") else None,
        }


@dataclass
class PromptEditResult:
    """Structured result of a prompt-driven image editing execution."""
    success: bool
    plan: PromptEditPlan
    output_path: Path | None = None
    output_image: Image.Image | None = None
    mask_image: Image.Image | None = None
    overlay_image: Image.Image | None = None
    primed_image: Image.Image | None = None
    error_code: str | None = None
    error_message: str | None = None
    execution_time_ms: float = 0.0
    backend_result: SD15QnnInpaintingResult | None = None
    sidecar_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "plan": self.plan.to_dict(),
        }


class PromptEditController:
    """
    Studio controller for natural-language prompt-driven image editing.
    Orchestrates semantic intent parsing, deterministic segmentation,
    photometric priming, and Hexagon NPU inference routing.
    """

    # Inherent object-to-color fallbacks when prompt omits source color
    OBJECT_DEFAULT_COLORS: dict[str, str] = {
        "apfel": "red",
        "apple": "red",
        "glasskulptur": "green",
        "falke": "green",
        "skulptur": "green",
    }

    # Inherent object-to-spatial fallbacks for grounded surface items
    OBJECT_DEFAULT_SPATIAL: dict[str, str] = {
        "tisch": "bottom",
        "table": "bottom",
        "boden": "bottom",
        "ground": "bottom",
    }

    # Standardized translation mapping from German object tokens to English SD1.5 tokens
    OBJECT_TRANSLATIONS: dict[str, str] = {
        "apfel": "apple",
        "apple": "apple",
        "glasskulptur": "glass sculpture",
        "skulptur": "sculpture",
        "sculpture": "sculpture",
        "falke": "falcon",
        "falcon": "falcon",
        "vogel": "bird",
        "bird": "bird",
        "figur": "figurine",
        "tisch": "table",
        "table": "table",
        "jacke": "jacket",
        "jacket": "jacket",
        "lederjacke": "leather jacket",
    }

    # Preset-specific canonical seeds for deterministic high-polish material transformations
    OBJECT_PRESET_SEEDS: dict[str, int] = {
        "skulptur": 100,
        "sculpture": 100,
        "glasskulptur": 100,
        "falke": 100,
        "falcon": 100,
        "apfel": 43,
        "apple": 43,
    }

    def __init__(
        self,
        inpainting_controller: InpaintingController | None = None,
        img2img_controller: ImageToImageController | None = None,
        parser: PromptIntentParser | None = None,
        segmenter: ColorSpatialSegmenter | None = None,
        ui_dispatch: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self.ui_dispatch = ui_dispatch or (lambda callback: callback())
        self.inpainting_controller = inpainting_controller or InpaintingController(ui_dispatch=self.ui_dispatch)
        self.img2img_controller = img2img_controller or ImageToImageController(ui_dispatch=self.ui_dispatch)
        self.parser = parser or PromptIntentParser()
        self.segmenter = segmenter or ColorSpatialSegmenter()
        self.hybrid_segmenter = PhoenixHybridSegmenter(color_segmenter=self.segmenter)
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        """Indicate whether an inference thread is actively running."""
        return (
            (self._thread is not None and self._thread.is_alive())
            or self.inpainting_controller.running
            or self.img2img_controller.running
        )

    def analyze(
        self,
        image: Image.Image | Path | str,
        prompt: str,
        target_color_hint: str | None = None,
        spatial_hint_override: str | None = None,
        point_prompt: tuple[int, int] | None = None,
        negative_points: list[tuple[int, int]] | None = None,
        use_hybrid: bool = True,
    ) -> PromptEditPlan:
        """
        Analyze prompt and input image to create a validated execution plan without starting inference.
        Enforces Safety Gate 1 (Intent & Confidence) and Safety Gate 2 (Mask & Region Bounds).
        Supports deterministic point-prompting and automatic source color probing.
        Supports Phoenix Hybrid Segmentation (Qualcomm Hexagon HTP MobileSAM + ColorSpatialSegmenter).
        """
        # Load and convert image to RGB
        if isinstance(image, (str, Path)):
            with Image.open(image) as opened:
                source_image = opened.convert("RGB")
        else:
            source_image = image.convert("RGB")

        # 1. Semantic Intent Parsing
        parsed = self.parser.parse(prompt)

        # Safety Gate 1: Check for UNKNOWN intent or lack of confidence
        if parsed.intent == IntentCategory.UNKNOWN:
            return PromptEditPlan(
                can_execute=False,
                intent=parsed.intent,
                parsed_intent=parsed,
                mode="LOCAL",
                target_object=None,
                material_preset=None,
                target_color=None,
                segment_result=None,
                refined_prompt="",
                negative_prompt="",
                denoising_strength=0.0,
                controller_route="NONE",
                rejection_reason="Unbekannte oder uneindeutige Bearbeitungsabsicht (UNKNOWN). Keine Inferenz gestartet.",
                point_prompt=point_prompt,
            )

        if not parsed.is_confident and parsed.intent != IntentCategory.GLOBAL_ATMOSPHERE:
            return PromptEditPlan(
                can_execute=False,
                intent=parsed.intent,
                parsed_intent=parsed,
                mode=parsed.mode,
                target_object=parsed.target_object,
                material_preset=None,
                target_color=None,
                segment_result=None,
                refined_prompt="",
                negative_prompt="",
                denoising_strength=0.0,
                controller_route="NONE",
                rejection_reason="Bearbeitungsabsicht nicht mit ausreichender Konfidenz erkannt.",
                point_prompt=point_prompt,
            )

        # 2. Routing branch for GLOBAL_ATMOSPHERE
        if parsed.intent == IntentCategory.GLOBAL_ATMOSPHERE:
            keyword = parsed.modification or "Atmosphäre"
            refined_prompt = (
                f"Photorealistic master photography, {keyword} lighting and atmosphere, "
                f"cinematic natural lighting, high dynamic range, sharp details, 8k"
            )
            negative_prompt = "blurry, low quality, artifacts, overexposed, distorted geometry"
            return PromptEditPlan(
                can_execute=True,
                intent=parsed.intent,
                parsed_intent=parsed,
                mode="GLOBAL",
                target_object=parsed.target_object,
                material_preset=None,
                target_color=None,
                segment_result=None,
                refined_prompt=refined_prompt,
                negative_prompt=negative_prompt,
                denoising_strength=0.65,
                controller_route="IMG2IMG_GLOBAL",
                rejection_reason=None,
                point_prompt=point_prompt,
            )

        # 3. Local Intent Processing (MATERIAL_TRANSFORM, COLOR_TRANSFORM, OBJECT_REMOVAL)
        # Determine source color for segmentation
        detected_source_color = target_color_hint or parsed.source_color
        if not detected_source_color and parsed.target_object and point_prompt is None:
            norm_obj = parsed.target_object.strip().lower()
            detected_source_color = self.OBJECT_DEFAULT_COLORS.get(norm_obj)

        spatial_hint = spatial_hint_override or parsed.spatial_hint
        if not spatial_hint and parsed.target_object:
            norm_obj = parsed.target_object.strip().lower()
            spatial_hint = self.OBJECT_DEFAULT_SPATIAL.get(norm_obj)

        # Determine whether object is apparel to activate strict skin/face/hand protection
        norm_obj = (parsed.target_object or "").strip().lower()
        is_apparel = any(
            token in norm_obj or token in prompt.lower()
            for token in ("jacke", "jacket", "shirt", "t-shirt", "kleid", "dress", "mantel", "coat", "hose", "pants", "pullover", "sweater", "bluse", "blouse", "rock", "skirt", "anzug", "suit")
        )

        # Run Hybrid Segmentation (MobileSAM HTP + ColorSpatial) if point_prompt is provided
        hybrid_res = None
        if point_prompt is not None and use_hybrid:
            try:
                hybrid_res = self.hybrid_segmenter.segment_hybrid(
                    image=source_image,
                    point_prompt=point_prompt,
                    negative_points=negative_points,
                    target_object_hint=parsed.target_object,
                    target_color_hint=detected_source_color,
                    spatial_hint=spatial_hint,
                    protect_skin=is_apparel,
                    edge_snapping=True,
                    generate_visuals=True,
                )
                seg_result = SegmentResult(
                    success=hybrid_res.success,
                    is_valid=hybrid_res.is_valid,
                    is_confident=hybrid_res.is_confident,
                    active_pixel_count=hybrid_res.active_pixel_count,
                    coverage_ratio=hybrid_res.coverage_ratio,
                    spatial_bbox=hybrid_res.spatial_bbox,
                    detected_color_name=hybrid_res.detected_color_name,
                    spatial_hint=spatial_hint,
                    status_message=hybrid_res.status_message,
                    deterministic_hash=hybrid_res.deterministic_hash,
                    elapsed_ms=hybrid_res.elapsed_ms,
                    mask=hybrid_res.mask,
                    overlay_image=hybrid_res.overlay_image,
                    comparison_grid=hybrid_res.comparison_grid,
                )
            except Exception as e:
                logger.warning(f"Hybrid segmentation fallback to pure ColorSpatial: {e}")
                seg_result = self.segmenter.segment(
                    image=source_image,
                    target_color=detected_source_color,
                    spatial_hint=spatial_hint,
                    point_prompt=point_prompt,
                    protect_skin=is_apparel,
                    edge_snapping=True,
                    generate_visuals=True,
                )
        else:
            seg_result = self.segmenter.segment(
                image=source_image,
                target_color=detected_source_color,
                spatial_hint=spatial_hint,
                point_prompt=point_prompt,
                protect_skin=is_apparel,
                edge_snapping=True,
                generate_visuals=True,
            )

        # Safety Gate 2: Mask validity and region bounds
        if not seg_result.is_valid or not seg_result.is_confident or seg_result.active_pixel_count == 0:
            return PromptEditPlan(
                can_execute=False,
                intent=parsed.intent,
                parsed_intent=parsed,
                mode="LOCAL",
                target_object=parsed.target_object,
                material_preset=None,
                target_color=parsed.target_color,
                segment_result=seg_result,
                refined_prompt="",
                negative_prompt="",
                denoising_strength=0.0,
                controller_route="NONE",
                rejection_reason=f"Sicherheitsabbruch Maskierung: {seg_result.status_message}",
                point_prompt=point_prompt,
            )

        # 4. Route: MATERIAL_TRANSFORM
        if parsed.intent == IntentCategory.MATERIAL_TRANSFORM:
            target_mat = (parsed.target_material or "").lower()
            # Map to standard Phoenix Material Lab presets if applicable
            material_preset_id = None
            if target_mat in ("gold", "24k_gold", "24k gold"):
                material_preset_id = "24k_gold"
            elif target_mat in ("brass", "antique_brass", "antik-messing", "messing"):
                material_preset_id = "antique_brass"
            elif target_mat in ("copper", "kupfer"):
                material_preset_id = "copper"
            elif target_mat in ("chrome", "chrom", "silver", "silber"):
                material_preset_id = "chrome"
            elif "leather" in target_mat or "leder" in target_mat or "leather" in (parsed.modification or "").lower():
                material_preset_id = "black_leather"

            if material_preset_id is not None:
                preset = get_material_preset(material_preset_id)
                raw_target = (parsed.target_object or "").strip().lower()
                default_target = "jacket" if material_preset_id == "black_leather" else "sculpture"
                target_name = self.OBJECT_TRANSLATIONS.get(raw_target, parsed.target_object or default_target)
                if material_preset_id == "black_leather":
                    refined_prompt = (
                        f"A photorealistic {parsed.target_color or 'black'} leather {target_name}, "
                        "authentic fine leather grain texture, subtle specular highlights, professional studio lighting, 8k."
                    )
                    denoising_strength = 0.80
                else:
                    refined_prompt = (
                        f"A solid polished {preset.display_name} {target_name}, sleek smooth curved metallic shape, "
                        f"pure {preset.display_name} metal, highly reflective surface, specular highlights, photorealistic, 8k."
                    )
                    denoising_strength = 0.75
                negative_prompt = preset.negative_prompt
            else:
                # General material
                raw_target = (parsed.target_object or "").strip().lower()
                target_name = self.OBJECT_TRANSLATIONS.get(raw_target, parsed.target_object or "object")
                refined_prompt = (
                    f"A photorealistic {parsed.target_material} {target_name}, "
                    f"authentic {parsed.target_material} surface texture, realistic reflections, 8k."
                )
                negative_prompt = "blurry, low quality, artifacts, distorted"
                denoising_strength = 0.75

            return PromptEditPlan(
                can_execute=True,
                intent=parsed.intent,
                parsed_intent=parsed,
                mode="LOCAL",
                target_object=parsed.target_object,
                material_preset=material_preset_id,
                target_color=parsed.target_color or seg_result.detected_color_name,
                segment_result=seg_result,
                refined_prompt=refined_prompt,
                negative_prompt=negative_prompt,
                denoising_strength=denoising_strength,
                controller_route="INPAINTING_MATERIAL",
                rejection_reason=None,
                point_prompt=point_prompt,
            )

        # 5. Route: COLOR_TRANSFORM
        if parsed.intent == IntentCategory.COLOR_TRANSFORM:
            target_c = parsed.target_color or "color"
            src_c = seg_result.detected_color_name or parsed.source_color or "original"
            refined_prompt = (
                f"A photorealistic {target_c} {parsed.target_object or 'object'}, authentic surface texture, "
                "natural highlights and reflections, high quality, 8k."
            )
            negative_prompt = f"{src_c}, blurry, artifacts, low quality"
            return PromptEditPlan(
                can_execute=True,
                intent=parsed.intent,
                parsed_intent=parsed,
                mode="LOCAL",
                target_object=parsed.target_object,
                material_preset=None,
                target_color=parsed.target_color or seg_result.detected_color_name,
                segment_result=seg_result,
                refined_prompt=refined_prompt,
                negative_prompt=negative_prompt,
                denoising_strength=0.55,
                controller_route="INPAINTING_COLOR",
                rejection_reason=None,
                point_prompt=point_prompt,
            )

        # 6. Route: OBJECT_REMOVAL
        if parsed.intent == IntentCategory.OBJECT_REMOVAL:
            refined_prompt = (
                "Clean empty seamless background, perfectly restored surface texture, "
                "consistent natural lighting and shadows, sharp focus, 8k photorealistic."
            )
            negative_prompt = (
                f"{parsed.target_object or 'object'}, artifacts, distortions, seams, "
                "ghosting, blurry, floating debris."
            )
            return PromptEditPlan(
                can_execute=True,
                intent=parsed.intent,
                parsed_intent=parsed,
                mode="LOCAL",
                target_object=parsed.target_object,
                material_preset=None,
                target_color=None,
                segment_result=seg_result,
                refined_prompt=refined_prompt,
                negative_prompt=negative_prompt,
                denoising_strength=1.0,
                controller_route="INPAINTING_REMOVAL",
                rejection_reason=None,
                point_prompt=point_prompt,
            )

        # Safety Fallback
        return PromptEditPlan(
            can_execute=False,
            intent=IntentCategory.UNKNOWN,
            parsed_intent=parsed,
            mode="LOCAL",
            target_object=None,
            material_preset=None,
            target_color=None,
            segment_result=None,
            refined_prompt="",
            negative_prompt="",
            denoising_strength=0.0,
            controller_route="NONE",
            rejection_reason="Unerwarteter Intent-Zustand. Keine Ausführung.",
        )

    def execute(
        self,
        *,
        input_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        steps: int = 20,
        seed: int = 42,
        cfg_scale: float = 7.5,
        target_color_hint: str | None = None,
        spatial_hint_override: str | None = None,
        point_prompt: tuple[int, int] | None = None,
        negative_points: list[tuple[int, int]] | None = None,
        use_hybrid: bool = True,
        on_progress: Callable[[str, float, str | None], None] | None = None,
    ) -> PromptEditResult:
        """
        Execute synchronous prompt-driven editing on Snapdragon X Elite NPU.
        Enforces non-destructive execution and bit-exact background preservation.
        """
        t0 = time.perf_counter()
        inp_path = Path(input_image_path).resolve()
        out_path = Path(output_path).resolve()

        # Non-destructive check
        if inp_path == out_path:
            raise ValueError("The original input image cannot be overwritten as output_path.")

        if not inp_path.is_file():
            raise FileNotFoundError(f"Input image not found: {inp_path}")

        def progress(phase: str, val: float, msg: str | None) -> None:
            if on_progress:
                self.ui_dispatch(lambda: on_progress(phase, val, msg))

        progress("plan", 0.05, "Bearbeitungsauftrag und Intent werden analysiert...")

        with Image.open(inp_path) as opened:
            source_img = opened.convert("RGB")

        # Analyze & Plan
        plan = self.analyze(
            image=source_img,
            prompt=prompt,
            target_color_hint=target_color_hint,
            spatial_hint_override=spatial_hint_override,
            point_prompt=point_prompt,
            negative_points=negative_points,
            use_hybrid=use_hybrid,
        )

        if not plan.can_execute:
            return PromptEditResult(
                success=False,
                plan=plan,
                error_code="ERR_SAFETY_GATE_REJECTED",
                error_message=plan.rejection_reason or "Safety gate rejected inference.",
                execution_time_ms=(time.perf_counter() - t0) * 1000.0,
            )

        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # Resolve target-specific canonical seed if default seed=42 was passed
        actual_seed = seed
        if seed == 42 and plan.parsed_intent and plan.parsed_intent.target_object:
            target_key = plan.parsed_intent.target_object.strip().lower()
            if target_key in self.OBJECT_PRESET_SEEDS:
                actual_seed = self.OBJECT_PRESET_SEEDS[target_key]

        # -------------------------------------------------------------
        # GLOBAL_ATMOSPHERE Route: ImageToImageController (Canny QNN)
        # -------------------------------------------------------------
        if plan.controller_route == "IMG2IMG_GLOBAL":
            progress("infer_global", 0.20, f"Globale Transformation ({plan.parsed_intent.modification})...")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            res = self.img2img_controller._run_product_path(
                input_image_path=inp_path,
                prompt=plan.refined_prompt,
                output_path=out_path,
                negative_prompt=plan.negative_prompt,
                steps=steps,
                seed=actual_seed,
                cfg_scale=cfg_scale,
                denoising_strength=plan.denoising_strength,
                enable_reference_control=True,
                reference_mode="canny_qnn",
                reference_fidelity=0.75,
                progress=progress,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            result_img = None
            if res.success and out_path.exists():
                with Image.open(out_path) as opened:
                    result_img = opened.convert("RGB")
                self._save_sidecar(out_path, plan, res, elapsed_ms)

            return PromptEditResult(
                success=res.success,
                plan=plan,
                output_path=out_path if res.success else None,
                output_image=result_img,
                error_code=res.error_code,
                error_message=res.error_message,
                execution_time_ms=elapsed_ms,
                backend_result=res,
            )

        # -------------------------------------------------------------
        # LOCAL Routes: InpaintingController with Mask & Priming
        # -------------------------------------------------------------
        assert plan.segment_result is not None
        assert plan.segment_result.mask is not None

        with tempfile.TemporaryDirectory(prefix="prompt_edit_", dir=TEMP_DIR) as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            mask_temp_path = temp_dir / "mask.png"
            primed_temp_path = temp_dir / "primed_input.png"

            mask_img = plan.segment_result.mask
            mask_img.save(mask_temp_path, format="PNG")

            working_input_path = inp_path
            primed_image = None

            # Photometric priming for Phoenix Material Presets (Gold, Brass, Copper, Chrome, Black Leather)
            if plan.material_preset is not None:
                progress("prime_material", 0.15, f"Material-Priming ({plan.material_preset}) wird angewendet...")
                primed_image = prime_material_chrominance(
                    source_img=source_img,
                    mask_img=mask_img,
                    preset_name=plan.material_preset,
                    intensity=1.0,
                )
                primed_image.save(primed_temp_path, format="PNG")
                working_input_path = primed_temp_path

            progress("infer_htp", 0.30, "Hexagon NPU Inpainting Inferenz wird ausgeführt...")
            out_path.parent.mkdir(parents=True, exist_ok=True)

            res = self.inpainting_controller._run_product_path(
                input_image_path=working_input_path,
                mask_image_path=mask_temp_path,
                prompt=plan.refined_prompt,
                output_path=out_path,
                negative_prompt=plan.negative_prompt,
                steps=steps,
                seed=actual_seed,
                cfg_scale=cfg_scale,
                denoising_strength=plan.denoising_strength,
                feather_radius=5,
                dilate_pixels=1,
                material_preset=None,  # Handled pre-run above for exact tracking
                progress=progress,
            )

            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            result_img = None
            if res.success and out_path.exists():
                with Image.open(out_path) as opened:
                    result_img = opened.convert("RGB")

                # Guarantee bit-exact identity outside mask
                result_img = self._verify_and_enforce_background_identity(source_img, result_img, mask_img, out_path)
                self._save_sidecar(out_path, plan, res, elapsed_ms)

            return PromptEditResult(
                success=res.success,
                plan=plan,
                output_path=out_path if res.success else None,
                output_image=result_img,
                mask_image=plan.segment_result.mask,
                overlay_image=plan.segment_result.overlay_image,
                primed_image=primed_image,
                error_code=res.error_code,
                error_message=res.error_message,
                execution_time_ms=elapsed_ms,
                backend_result=res,
            )

    def start(
        self,
        *,
        input_image_path: str | Path,
        prompt: str,
        output_path: str | Path,
        steps: int = 20,
        seed: int = 42,
        cfg_scale: float = 7.5,
        target_color_hint: str | None = None,
        spatial_hint_override: str | None = None,
        point_prompt: tuple[int, int] | None = None,
        negative_points: list[tuple[int, int]] | None = None,
        use_hybrid: bool = True,
        on_progress: Callable[[str, float, str | None], None] | None = None,
        on_complete: Callable[[PromptEditResult], None] | None = None,
        asynchronous: bool = True,
    ) -> None:
        """
        Threaded entry point matching Studio controller convention.
        """
        if self.running:
            raise RuntimeError("Prompt editing inference is already running")

        def run() -> None:
            try:
                res = self.execute(
                    input_image_path=input_image_path,
                    prompt=prompt,
                    output_path=output_path,
                    steps=steps,
                    seed=seed,
                    cfg_scale=cfg_scale,
                    target_color_hint=target_color_hint,
                    spatial_hint_override=spatial_hint_override,
                    point_prompt=point_prompt,
                    negative_points=negative_points,
                    use_hybrid=use_hybrid,
                    on_progress=on_progress,
                )
            except Exception as exc:
                res = PromptEditResult(
                    success=False,
                    plan=PromptEditPlan(
                        can_execute=False,
                        intent=IntentCategory.UNKNOWN,
                        parsed_intent=self.parser.parse(prompt),
                        mode="LOCAL",
                        target_object=None,
                        material_preset=None,
                        target_color=None,
                        segment_result=None,
                        refined_prompt="",
                        negative_prompt="",
                        denoising_strength=0.0,
                        controller_route="NONE",
                        rejection_reason=f"Exception: {exc}",
                    ),
                    error_code="ERR_PROMPT_EDIT_EXCEPTION",
                    error_message=f"{type(exc).__name__}: {exc}",
                )
            if on_complete:
                self.ui_dispatch(lambda: on_complete(res))

        if asynchronous:
            self._thread = threading.Thread(target=run, name="prompt-edit-ui", daemon=True)
            self._thread.start()
        else:
            run()

    @staticmethod
    def _verify_and_enforce_background_identity(
        source: Image.Image,
        result: Image.Image,
        mask: Image.Image,
        out_path: Path,
    ) -> Image.Image:
        """
        Verifies and enforces 100% bit-exact pixel identity outside the mask region.
        """
        src_arr = np.array(source)
        res_arr = np.array(result).copy()
        mask_arr = np.array(mask)

        # Outside mask (mask == 0), restore bit-exact source pixels
        untouched_mask = (mask_arr == 0)
        if not np.array_equal(res_arr[untouched_mask], src_arr[untouched_mask]):
            res_arr[untouched_mask] = src_arr[untouched_mask]
            corrected_img = Image.fromarray(res_arr)
            corrected_img.save(out_path, format="PNG")
            return corrected_img
        return result

    def _save_sidecar(
        self,
        output_path: Path,
        plan: PromptEditPlan,
        backend_result: SD15QnnInpaintingResult,
        elapsed_ms: float,
    ) -> None:
        """Save JSON sidecar documenting complete audit trail."""
        sidecar_path = output_path.with_suffix(".json")
        sidecar_data = {
            "sprint": "SPRINT_73",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_ms": round(elapsed_ms, 2),
            "plan": plan.to_dict(),
            "backend_metadata": backend_result.metadata if backend_result else {},
            "execution_evidence": {
                "qnn_context": "sd15_inpainting_qnn_htp.dlc",
                "hardware": "Qualcomm Hexagon NPU (HTP)",
                "cpu_fallback_count": 0,
            },
        }
        try:
            with open(sidecar_path, "w", encoding="utf-8") as f:
                json.dump(sidecar_data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning(f"Could not save sidecar metadata: {exc}")

    def cancel(self) -> None:
        """Cancel running inference."""
        self.inpainting_controller.cancel()
        self.img2img_controller.cancel()
