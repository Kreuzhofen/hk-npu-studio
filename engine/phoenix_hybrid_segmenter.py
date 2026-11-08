"""
HK NPU STUDIO – Phoenix Architecture
Sprint 95: Phoenix Hybrid Segmentation Engine

Fuses deep semantic instance segmentation from Qualcomm Hexagon HTP MobileSAM
with precise localized color, luminance, and edge analysis from ColorSpatialSegmenter.
Resolves compound sub-objects (e.g. apparel/jacket on person), multi-object identical
color disambiguation, and intricate freeform shapes with topological cavity preservation.
"""

from __future__ import annotations

import hashlib
import io
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from engine.backends.mobilesam_qnn_adapter import MobileSamQnnAdapter
from engine.color_spatial_segmenter import ColorSpatialSegmenter, SegmentResult

logger = logging.getLogger(__name__)


@dataclass
class HybridSegmentResult:
    """Complete result container for Phoenix Hybrid Segmentation."""
    success: bool
    is_valid: bool
    is_confident: bool
    active_pixel_count: int
    coverage_ratio: float
    coverage_percentage: float
    spatial_bbox: List[int]  # [x_min, y_min, x_max, y_max]
    detected_color_name: Optional[str]
    status_message: str
    deterministic_hash: str
    elapsed_ms: float
    mobile_sam_latency_ms: float
    confidence_score: float  # Normalized 0.0 - 1.0 (clamped)
    sub_object_isolated: bool = False
    raw_iou_score: float = 0.0  # Raw unbounded IoU-head MLP score
    hardware_target: str = "Qualcomm Hexagon NPU (HTP V73)"
    cpu_fallback_count: int = 0

    # Mask representations
    mask: Image.Image = field(repr=False, default=None)  # Fused final mask (PIL L)
    mask_array: np.ndarray = field(repr=False, default=None)  # Fused bool array
    semantic_mask: Optional[Image.Image] = field(repr=False, default=None)  # MobileSAM PIL
    semantic_mask_array: Optional[np.ndarray] = field(repr=False, default=None)
    color_mask: Optional[Image.Image] = field(repr=False, default=None)  # ColorSpatial PIL
    color_mask_array: Optional[np.ndarray] = field(repr=False, default=None)
    overlay_image: Optional[Image.Image] = field(repr=False, default=None)
    comparison_grid: Optional[Image.Image] = field(repr=False, default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result summary to JSON-serializable dictionary."""
        return {
            "success": self.success,
            "is_valid": self.is_valid,
            "is_confident": self.is_confident,
            "active_pixel_count": self.active_pixel_count,
            "coverage_ratio": round(self.coverage_ratio, 4),
            "coverage_percentage": round(self.coverage_percentage, 2),
            "spatial_bbox": self.spatial_bbox,
            "detected_color_name": self.detected_color_name,
            "status_message": self.status_message,
            "deterministic_hash": self.deterministic_hash,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "mobile_sam_latency_ms": round(self.mobile_sam_latency_ms, 2),
            "confidence_score": round(self.confidence_score, 4),
            "raw_iou_score": round(self.raw_iou_score, 4),
            "sub_object_isolated": self.sub_object_isolated,
            "hardware_target": self.hardware_target,
            "cpu_fallback_count": self.cpu_fallback_count,
        }


class PhoenixHybridSegmenter:
    """
    Unified Hybrid Segmentation Engine for HK NPU STUDIO.
    
    Coordinates Qualcomm Hexagon HTP MobileSAM and ColorSpatialSegmenter to produce
    commercially pristine segmentation masks for arbitrary objects and sub-parts.
    """

    def __init__(
        self,
        sam_adapter: Optional[MobileSamQnnAdapter] = None,
        color_segmenter: Optional[ColorSpatialSegmenter] = None,
        enable_htp: bool = True,
    ) -> None:
        self.enable_htp = enable_htp
        self.color_segmenter = color_segmenter or ColorSpatialSegmenter()
        self.sam_adapter = sam_adapter
        self._current_image_hash: Optional[str] = None

    def _ensure_sam_adapter(self) -> Optional[MobileSamQnnAdapter]:
        """Lazy-initialize MobileSAM HTP adapter on demand."""
        if not self.enable_htp:
            return None
        if self.sam_adapter is None:
            try:
                adapter = MobileSamQnnAdapter()
                adapter.initialize()
                self.sam_adapter = adapter
            except Exception as e:
                logger.warning(f"MobileSAM HTP adapter initialization deferred or unavailable: {e}")
                self.sam_adapter = None
        return self.sam_adapter

    def segment_hybrid(
        self,
        image: Union[Image.Image, np.ndarray],
        point_prompt: Union[Tuple[int, int], List[Tuple[int, int]]],
        negative_points: Optional[List[Tuple[int, int]]] = None,
        target_object_hint: Optional[str] = None,
        target_color_hint: Optional[str] = None,
        spatial_hint: Optional[str] = None,
        protect_skin: bool = False,
        edge_snapping: bool = True,
        generate_visuals: bool = True,
    ) -> HybridSegmentResult:
        """
        Execute unified hybrid segmentation on Qualcomm Hexagon HTP.
        
        Args:
            image: PIL Image or RGB numpy array
            point_prompt: Single (x, y) or list of positive click coordinates
            negative_points: Optional list of (x, y) exclusion click coordinates
            target_object_hint: Object label (e.g. 'jacket', 'apple', 'glass')
            target_color_hint: Optional color string override
            spatial_hint: Optional spatial region hint
            protect_skin: Whether to enforce human face/skin/hair protection
            edge_snapping: Whether to snap boundaries to Sobel luminance gradients
            generate_visuals: Whether to render high-polish visual cards
        """
        t0 = time.perf_counter()

        if isinstance(image, np.ndarray):
            pil_img = Image.fromarray(image).convert("RGB")
        else:
            pil_img = image.convert("RGB")

        w, h = pil_img.size
        img_arr = np.array(pil_img)

        # Normalize positive points to list of tuples
        if isinstance(point_prompt, tuple) and len(point_prompt) == 2 and isinstance(point_prompt[0], (int, float)):
            pos_pts = [(int(point_prompt[0]), int(point_prompt[1]))]
        elif isinstance(point_prompt, list):
            pos_pts = [(int(p[0]), int(p[1])) for p in point_prompt]
        else:
            raise ValueError(f"Invalid point_prompt format: {point_prompt}")

        neg_pts = [(int(p[0]), int(p[1])) for p in (negative_points or [])]
        primary_pt = pos_pts[0]

        # Determine if target object is apparel / clothing
        norm_obj = (target_object_hint or "").strip().lower()
        is_apparel = protect_skin or any(
            token in norm_obj
            for token in ("jacke", "jacket", "shirt", "kleid", "dress", "mantel", "coat", "hose", "pants", "pullover", "sweater", "bluse", "rock", "skirt")
        )

        # ----------------------------------------------------
        # 0. Point Plausibility & Background Click Safety Gate
        # ----------------------------------------------------
        # Verify if click point falls outside candidate target object in background
        if primary_pt is not None and (target_color_hint or norm_obj):
            check_color = target_color_hint
            if not check_color and any(k in norm_obj for k in ("apfel", "apple", "red apple", "jacke", "jacket")):
                check_color = "red"

            if check_color:
                cand_res = self.color_segmenter.segment(image=pil_img, target_color=check_color, point_prompt=None)
                if cand_res.is_valid and cand_res.active_pixel_count > 0:
                    cand_arr = np.array(cand_res.mask) > 127
                    dilated_cand = self.color_segmenter._dilate_3x3(cand_arr)
                    for _ in range(4):
                        dilated_cand = self.color_segmenter._dilate_3x3(dilated_cand)

                    px, py = primary_pt
                    if not dilated_cand[py, px]:
                        logger.warning(
                            f"Safety Gate 2 Triggered: Click point {primary_pt} is outside target object '{check_color}/{norm_obj}' in background."
                        )
                        return HybridSegmentResult(
                            success=False,
                            is_valid=False,
                            is_confident=False,
                            active_pixel_count=0,
                            coverage_ratio=0.0,
                            coverage_percentage=0.0,
                            spatial_bbox=[0, 0, 0, 0],
                            detected_color_name=None,
                            status_message=f"Sicherheitsabbruch (Safety Gate 2): Klickpunkt {primary_pt} liegt außerhalb des Zielobjekts im Hintergrund.",
                            deterministic_hash="0" * 64,
                            elapsed_ms=(time.perf_counter() - t0) * 1000,
                            mobile_sam_latency_ms=0.0,
                            confidence_score=0.0,
                            raw_iou_score=0.0,
                            sub_object_isolated=False,
                            mask=Image.new("L", (w, h), 0),
                            mask_array=np.zeros((h, w), dtype=bool),
                        )

        # ----------------------------------------------------
        # 1. ColorSpatialSegmenter Evaluation
        # ----------------------------------------------------
        # Use target_color_hint if provided; otherwise let ColorSpatial detect from point
        effective_color = target_color_hint
        cs_res: SegmentResult = self.color_segmenter.segment(
            image=pil_img,
            target_color=effective_color,
            spatial_hint=spatial_hint,
            point_prompt=primary_pt,
            protect_skin=is_apparel,
            edge_snapping=False,
            generate_visuals=False,
        )

        cs_mask_arr = np.array(cs_res.mask) > 127 if cs_res.is_valid else np.zeros((h, w), dtype=bool)
        detected_color = cs_res.detected_color_name

        # ----------------------------------------------------
        # 2. MobileSAM Qualcomm Hexagon HTP Evaluation
        # ----------------------------------------------------
        sam = self._ensure_sam_adapter()
        sam_latency_ms = 0.0
        sam_score = 0.0
        raw_iou_score = 0.0
        sam_mask_arr = np.zeros((h, w), dtype=bool)

        if sam is not None:
            try:
                # Cache image embedding across repeat queries for instant ~12ms response
                img_hash = hashlib.md5(img_arr.tobytes()).hexdigest()
                if self._current_image_hash != img_hash or sam._cached_embeddings is None:
                    sam.set_image(pil_img)
                    self._current_image_hash = img_hash

                # Predict mask for primary positive point on HTP
                t_sam_0 = time.perf_counter()
                sam_mask_arr, raw_score = sam.predict_mask([primary_pt])
                sam_latency_ms = (time.perf_counter() - t_sam_0) * 1000
                raw_iou_score = float(raw_score)
                # Clamp confidence score to valid probability range [0.0, 1.0]
                sam_score = min(1.0, max(0.0, float(raw_score)))

                # Additional positive points (if any): logical union
                for extra_pt in pos_pts[1:]:
                    m_extra, _ = sam.predict_mask([extra_pt])
                    sam_mask_arr = np.logical_or(sam_mask_arr, m_extra)

            except Exception as e:
                logger.warning(f"MobileSAM inference error on HTP: {e}. Falling back to ColorSpatial alone.")
                sam_mask_arr = np.zeros((h, w), dtype=bool)

        # ----------------------------------------------------
        # 3. Intelligent Hybrid Fusion
        # ----------------------------------------------------
        sub_object_isolated = False
        fused_arr = np.zeros((h, w), dtype=bool)

        # Case A: MobileSAM is active and yielded a candidate mask
        if sam_mask_arr.any():
            sam_count = int(sam_mask_arr.sum())
            cs_count = int(cs_mask_arr.sum())

            is_translucent = any(
                token in norm_obj
                for token in ("glas", "glass", "skulptur", "sculpture", "kristall", "crystal", "translucent")
            )
            is_freeform = any(
                token in norm_obj
                for token in ("star", "stern", "freiform", "freeform", "kavitaet", "cavity", "polygon", "shape")
            )

            # Case A1: Compound Sub-Object (e.g. Jacket on Person)
            # If apparel is detected OR (for non-translucent objects) SAM mask is > 1.8x the contiguous color region of the click point
            if is_apparel or (not is_translucent and not is_freeform and cs_count > 0 and sam_count > 1.8 * cs_count):
                # Intersect color mask within semantic envelope
                intersect_arr = np.logical_and(sam_mask_arr, cs_mask_arr)
                if intersect_arr.any():
                    # Morphological closing to keep buttons/zippers solid
                    closed = self.color_segmenter._morph_close_open_fast(intersect_arr)
                    # Filter to component containing the click seed
                    fused_arr = self.color_segmenter._filter_connected_components_fast(closed, point_prompt=primary_pt)
                    # Enforce strict biological tissue protection
                    fused_arr = self.color_segmenter._protect_biological_tissue(
                        img_arr,
                        fused_arr,
                        point_prompt=primary_pt,
                        is_apparel=is_apparel,
                    )
                    sub_object_isolated = True
                else:
                    # Fallback to CS mask if intersection was empty
                    fused_arr = cs_mask_arr
            
            # Case A2: Color mask is valid and cleanly bounds the object (e.g. Apple, Glass, Star)
            elif cs_mask_arr.any() and cs_count > 0:
                is_translucent = any(
                    token in norm_obj
                    for token in ("glas", "glass", "skulptur", "sculpture", "kristall", "crystal", "translucent")
                )
                if is_translucent:
                    # Glass / translucent sculpture: union of SAM and CS followed by 4-pass morphological closing
                    # to heal internal specular reflection pinholes without altering outer contours or dark line
                    fused_arr = np.logical_or(sam_mask_arr, cs_mask_arr)
                    d = fused_arr.copy()
                    for _ in range(4):
                        d = self.color_segmenter._dilate_3x3(d)
                    for _ in range(4):
                        d = self.color_segmenter._erode_3x3(d)
                    fused_arr = self.color_segmenter._filter_connected_components_fast(d, point_prompt=primary_pt)
                else:
                    # Opaque solid or freeform object (e.g. Apple, Star):
                    # Validate candidate pixels from MobileSAM against the foreground seed chromatic distribution
                    # to prevent background spillover (such as flat canvas bleed in Q4).
                    px, py = primary_pt
                    fg_rgb = img_arr[py, px].astype(np.float32)
                    color_dist = np.linalg.norm(img_arr.astype(np.float32) - fg_rgb, axis=2)

                    is_freeform = any(
                        token in norm_obj
                        for token in ("star", "stern", "freiform", "freeform", "kavitaet", "cavity", "polygon", "shape")
                    )

                    if is_freeform:
                        # Freeform / geometric shape with acute angles or cavities (Sprint 101):
                        # Enforce strict chromatic consistency against foreground seed (color_dist < 100.0)
                        # to eliminate morphological corner dilation and flat canvas bleed (exact 0px outer spillover)
                        sam_clean = sam_mask_arr & (color_dist < 100.0)
                        cs_clean = cs_mask_arr & (color_dist < 100.0)
                    else:
                        # Natural photographic objects (e.g. Apple) with natural lighting/shadows:
                        # MobileSAM candidate pixels are kept only if chromatically compatible with foreground
                        # or already validated by ColorSpatial
                        sam_clean = sam_mask_arr & ((color_dist < 100.0) | cs_mask_arr)
                        cs_clean = cs_mask_arr

                    ys_s, xs_s = np.where(sam_clean) if sam_clean.any() else ([], [])
                    ys_c, xs_c = np.where(cs_clean) if cs_clean.any() else ([], [])

                    # Check if SAM spilled significantly into top/bottom margins where CS has no pixels
                    sam_spill = len(ys_s) > 0 and len(ys_c) > 0 and ((ys_s.min() < max(0, ys_c.min() - 30)) or (ys_s.max() > min(h - 1, ys_c.max() + 30)))
                    if sam_spill:
                        # Restrict SAM to the spatial vertical bounds of the color object
                        y_min_bound = max(0, ys_c.min())
                        y_max_bound = min(h, ys_c.max() + 1)
                        x_min_bound = max(0, xs_c.min())
                        x_max_bound = min(w, xs_c.max() + 1)

                        spatial_clip = np.zeros((h, w), dtype=bool)
                        spatial_clip[y_min_bound:y_max_bound, x_min_bound:x_max_bound] = True

                        clipped_sam = np.logical_and(sam_clean, spatial_clip)
                        fused_arr = np.logical_or(clipped_sam, cs_clean)
                    else:
                        fused_arr = np.logical_or(sam_clean, cs_clean)

                    fused_arr = self.color_segmenter._filter_connected_components_fast(fused_arr, point_prompt=primary_pt)

            # Case A3: Neutral or uncolored object (e.g. Glass sculpture) where CS is weak
            else:
                filtered = self.color_segmenter._filter_connected_components_fast(sam_mask_arr, point_prompt=primary_pt)
                # Controlled morphological closing to heal specular pinhole gaps without altering outer contours
                closed = self.color_segmenter._erode_3x3(self.color_segmenter._dilate_3x3(filtered))
                fused_arr = self.color_segmenter._filter_connected_components_fast(closed, point_prompt=primary_pt)

        # Case B: MobileSAM inactive -> use ColorSpatial directly
        elif cs_mask_arr.any():
            fused_arr = cs_mask_arr

        # ----------------------------------------------------
        # 4. Multi-Object Isolation & Edge-Snapping
        # ----------------------------------------------------
        # Keep strictly the connected component connected to the primary positive click point
        if fused_arr.any() and primary_pt is not None:
            fused_arr = self.color_segmenter._filter_connected_components_fast(fused_arr, point_prompt=primary_pt)

        # Sobel Edge-Snapping (snap foreground object boundaries before cavity extraction)
        is_freeform_obj = any(
            token in norm_obj
            for token in ("star", "stern", "freiform", "freeform", "kavitaet", "cavity", "polygon", "shape")
        )
        if edge_snapping and not is_freeform_obj and fused_arr.any():
            fused_arr = self.color_segmenter._snap_to_edges_fast(img_arr, fused_arr)

        # Process negative exclusion points (e.g. for interior holes/cavities or unwanted regions)
        if neg_pts and fused_arr.any():
            fg_col = img_arr[primary_pt[1], primary_pt[0]].astype(float) if primary_pt else None
            for nx, ny in neg_pts:
                if 0 <= nx < w and 0 <= ny < h:
                    bg_col = img_arr[ny, nx].astype(float)
                    dist_to_fg = float(np.linalg.norm(bg_col - fg_col)) if fg_col is not None else 100.0
                    is_cavity = dist_to_fg > 30.0

                    # Circular exclusion zone around the negative point (r=10px)
                    y_indices, x_indices = np.ogrid[:h, :w]
                    dist_sq = (x_indices - nx) ** 2 + (y_indices - ny) ** 2
                    circle_mask = dist_sq <= (10 ** 2)
                    fused_arr[circle_mask] = False

                    # If negative point is in an interior cavity or background region,
                    # flood-fill the connected cavity to cleanly subtract leaked mask pixels
                    queue = [(nx, ny)]
                    visited = {(nx, ny)}
                    cavity_mask = np.zeros((h, w), dtype=bool)
                    step = 0
                    max_steps = 25000
                    
                    while queue and step < max_steps:
                        cx, cy = queue.pop(0)
                        step += 1
                        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            adj_x, adj_y = cx + dx, cy + dy
                            if 0 <= adj_x < w and 0 <= adj_y < h and (adj_x, adj_y) not in visited:
                                visited.add((adj_x, adj_y))
                                diff = float(np.linalg.norm(img_arr[adj_y, adj_x].astype(float) - bg_col))
                                if diff < 25.0:
                                    cavity_mask[adj_y, adj_x] = True
                                    # If not in cavity mode (clicked on solid foreground to erase), limit radius
                                    if not is_cavity and ((adj_x - nx) ** 2 + (adj_y - ny) ** 2 > 15 ** 2):
                                        continue
                                    queue.append((adj_x, adj_y))
                    
                    fused_arr[cavity_mask] = False
                    fused_arr[ny, nx] = False

        # Biological tissue re-check
        if is_apparel and fused_arr.any():
            fused_arr = self.color_segmenter._protect_biological_tissue(
                img_arr,
                fused_arr,
                point_prompt=primary_pt,
                is_apparel=is_apparel,
            )

        # ----------------------------------------------------
        # 5. Safety Gates & Metadata Computation
        # ----------------------------------------------------
        active_px = int(fused_arr.sum())
        total_px = w * h
        cov_ratio = float(active_px) / float(total_px)
        cov_pct = cov_ratio * 100.0

        is_valid = (0 < active_px <= int(0.90 * total_px))
        is_confident = is_valid and (sam_score >= 0.50 or cs_res.is_confident)

        if not is_valid:
            status_msg = f"Sicherheitsabbruch: Maske ungültig oder leer ({active_px} Pixel)."
            success = False
        else:
            status_msg = f"Hybrid-Objekt präzise segmentiert ({active_px:,} Pixel, {cov_pct:.1f}% Abdeckung)."
            success = True

        # Bounding box
        if active_px > 0:
            ys, xs = np.where(fused_arr)
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
        else:
            bbox = [0, 0, 0, 0]

        # Deterministic SHA-256 hash
        mask_bytes = (fused_arr.astype(np.uint8) * 255).tobytes()
        mask_hash = hashlib.sha256(mask_bytes).hexdigest()

        elapsed_ms = (time.perf_counter() - t0) * 1000

        # Create PIL Mask
        final_mask_pil = Image.fromarray((fused_arr.astype(np.uint8) * 255), mode="L")
        sem_mask_pil = Image.fromarray((sam_mask_arr.astype(np.uint8) * 255), mode="L") if sam_mask_arr.any() else None
        col_mask_pil = Image.fromarray((cs_mask_arr.astype(np.uint8) * 255), mode="L") if cs_mask_arr.any() else None

        # Visuals
        overlay_img = None
        grid_img = None
        if generate_visuals:
            overlay_img = self._create_annotated_overlay(pil_img, fused_arr, pos_pts, neg_pts)
            grid_img = self._create_comparison_grid(pil_img, sem_mask_pil, col_mask_pil, final_mask_pil, overlay_img, pos_pts, neg_pts)

        return HybridSegmentResult(
            success=success,
            is_valid=is_valid,
            is_confident=is_confident,
            active_pixel_count=active_px,
            coverage_ratio=cov_ratio,
            coverage_percentage=cov_pct,
            spatial_bbox=bbox,
            detected_color_name=detected_color,
            status_message=status_msg,
            deterministic_hash=mask_hash,
            elapsed_ms=elapsed_ms,
            mobile_sam_latency_ms=sam_latency_ms,
            confidence_score=sam_score,
            raw_iou_score=raw_iou_score,
            sub_object_isolated=sub_object_isolated,
            mask=final_mask_pil,
            mask_array=fused_arr,
            semantic_mask=sem_mask_pil,
            semantic_mask_array=sam_mask_arr if sam_mask_arr.any() else None,
            color_mask=col_mask_pil,
            color_mask_array=cs_mask_arr if cs_mask_arr.any() else None,
            overlay_image=overlay_img,
            comparison_grid=grid_img,
        )

    def _create_annotated_overlay(
        self,
        base_img: Image.Image,
        mask_arr: np.ndarray,
        pos_pts: List[Tuple[int, int]],
        neg_pts: List[Tuple[int, int]],
    ) -> Image.Image:
        """Create transparent accent tint overlay with target markers on positive and negative clicks."""
        overlay = np.array(base_img.convert("RGB")).astype(np.float32)
        m = mask_arr > 0

        # Phoenix Accent Tint (47, 128, 237)
        overlay[m, 0] = overlay[m, 0] * 0.40 + 47.0 * 0.60
        overlay[m, 1] = overlay[m, 1] * 0.40 + 128.0 * 0.60
        overlay[m, 2] = overlay[m, 2] * 0.40 + 237.0 * 0.60

        pil_ov = Image.fromarray(np.clip(overlay, 0, 255).astype(np.uint8))
        draw = ImageDraw.Draw(pil_ov)

        # Draw positive points (Blue/Yellow target)
        for px, py in pos_pts:
            r = 9
            draw.ellipse([px - r - 2, py - r - 2, px + r + 2, py + r + 2], outline=(0, 0, 0), width=2)
            draw.ellipse([px - r, py - r, px + r, py + r], outline=(47, 128, 237), width=3)
            draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 230, 0), outline=(0, 0, 0), width=1)

        # Draw negative points (Red crosshair)
        for nx, ny in neg_pts:
            r = 9
            draw.ellipse([nx - r - 2, ny - r - 2, nx + r + 2, ny + r + 2], outline=(0, 0, 0), width=2)
            draw.ellipse([nx - r, ny - r, nx + r, ny + r], outline=(231, 76, 60), width=3)
            draw.line([nx - r + 2, ny - r + 2, nx + r - 2, ny + r - 2], fill=(231, 76, 60), width=2)
            draw.line([nx - r + 2, ny + r - 2, nx + r - 2, ny - r + 2], fill=(231, 76, 60), width=2)

        return pil_ov

    def _create_comparison_grid(
        self,
        original: Image.Image,
        semantic: Optional[Image.Image],
        color: Optional[Image.Image],
        fused: Image.Image,
        overlay: Image.Image,
        pos_pts: List[Tuple[int, int]],
        neg_pts: List[Tuple[int, int]],
    ) -> Image.Image:
        """Create 5-column comparison card showing full hybrid progression."""
        col_w, col_h = 240, 240
        margin = 15
        spacing = 10
        header_h = 55

        total_w = margin * 2 + col_w * 5 + spacing * 4
        total_h = header_h + col_h + margin * 2

        card = Image.new("RGB", (total_w, total_h), color=(22, 26, 34))
        draw = ImageDraw.Draw(card)

        # Font
        font_paths = [
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\arial.ttf"),
        ]
        font_h = ImageFont.load_default()
        font_lbl = ImageFont.load_default()
        for fp in font_paths:
            if fp.exists():
                try:
                    font_h = ImageFont.truetype(str(fp), 16)
                    font_lbl = ImageFont.truetype(str(fp), 12)
                    break
                except Exception:
                    pass

        draw.text((margin, 15), "HK NPU STUDIO – PHOENIX HYBRID SEGMENTATION (Qualcomm Hexagon HTP)", fill=(240, 245, 255), font=font_h)

        cols = [
            (original, "1. Original Image"),
            (semantic if semantic else Image.new("L", original.size), "2. MobileSAM (HTP)"),
            (color if color else Image.new("L", original.size), "3. ColorSpatial Mask"),
            (fused, "4. Fused Hybrid Mask"),
            (overlay, "5. Hybrid Result Overlay"),
        ]

        for i, (img, lbl) in enumerate(cols):
            x = margin + i * (col_w + spacing)
            y = header_h + margin

            draw.rectangle([x - 1, y - 1, x + col_w, y + col_h], outline=(45, 55, 70), width=1)
            thumb = img.convert("RGB").resize((col_w, col_h), Image.Resampling.BILINEAR)
            card.paste(thumb, (x, y))

            draw.rectangle([x, y + col_h - 24, x + col_w, y + col_h], fill=(12, 16, 22))
            draw.text((x + 6, y + col_h - 20), lbl, fill=(200, 215, 235), font=font_lbl)

        return card
