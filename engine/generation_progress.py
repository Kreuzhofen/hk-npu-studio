from __future__ import annotations

import re

from app.i18n import tr
from engine.job_lifecycle import set_job_progress


_QNN_STAGE_RULES = (
    ("Preparing Qualcomm QNN", 0.05, "npu_preparing", "NPU wird vorbereitet..."),
    ("Loading Text Encoder", 0.10, "model_loading_text_encoder", "Modell wird geladen (Text Encoder)..."),
    ("Loading UNet", 0.15, "model_loading_unet", "Modell wird geladen (UNet)..."),
    ("Loading VAE", 0.20, "model_loading_vae", "Modell wird geladen (VAE)..."),
    ("Tokenizing prompt", 0.25, "model_loading", "Modell wird geladen..."),
    ("Computing Canny edge image", 0.30, "controlnet_preprocessing", "ControlNet Vorverarbeitung..."),
    ("Decoding image", 0.90, "vae_decoding", "VAE Decoding..."),
    ("Saving image", 0.95, "saving_image", "Bild wird gespeichert & Metadaten geschrieben..."),
)
_STEP_PATTERN = re.compile(r"Step\s+(\d+)/(\d+)")


def report_qnn_progress(job, output_line: str) -> bool:
    """Übersetzt QNN-Worker-Ausgaben in einheitliche Fortschrittsmeldungen."""
    match = _STEP_PATTERN.search(output_line)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        if total <= 0:
            return False
        sampling_progress = current / total
        progress = 0.30 + (sampling_progress * 0.55)
        message = tr(
            "sampling_phase",
            "Sampling Phase (Schritt {curr}/{total})...",
            curr=current,
            total=total,
        )
        set_job_progress(job, progress, message)
        return True

    for marker, progress, key, fallback in _QNN_STAGE_RULES:
        if marker in output_line:
            set_job_progress(job, progress, tr(key, fallback))
            return True
    return False
