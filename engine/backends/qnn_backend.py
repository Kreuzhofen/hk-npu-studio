"""
SnapdragonAI Studio

QNN Backend

Created by Holger Kreuzhofen
Phoenix Engine
"""

from pathlib import Path
import numpy as np
from PIL import Image


class QNNBackend:
    """
    Backend für Qualcomm AI Engine (QNN).

    Diese Klasse kapselt später sämtliche Kommunikation
    mit qnn-net-run und den QNN-Modellen.
    """

    def __init__(self):
        self.base_path = Path(r"C:\SnapdragonAI")
        self.input_dir = self.base_path / "input"
        self.output_dir = self.base_path / "output"

    def prepare_input(self, image_path):
        """
        Bereitet ein Bild für das QNN-Modell vor.
        """

        image = Image.open(image_path).convert("RGB")

        image = np.asarray(image).astype(np.float32)
        image /= 255.0

        # HWC -> CHW
        image = np.transpose(image, (2, 0, 1))

        # CHW -> NCHW
        image = np.expand_dims(image, axis=0)

        return image

    def upscale(self, image_path):
        """
        Führt später ein RealESRGAN-Upscaling aus.

        Aktuell nur Platzhalter.
        """

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(image_path)

        return {
            "status": "backend_ready",
            "image": str(image_path),
            "backend": "QNN"
        }