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
        Bereitet ein Bild für das QNN-RealESRGAN-Modell vor.
        """

        image = Image.open(image_path).convert("RGB")
        image = image.resize((128, 128))

        arr = np.asarray(image).astype(np.float32) / 255.0
        arr = arr.reshape(1, 128, 128, 3)

        return arr

    def write_raw_input(self, tensor):
        """
        Schreibt den vorbereiteten Tensor als RAW-Datei und erzeugt
        die input_list.txt für qnn-net-run.
        """

        raw_input = self.input_dir / "image.raw"
        input_list = self.input_dir / "input_list.txt"

        self.input_dir.mkdir(parents=True, exist_ok=True)

        tensor.tofile(raw_input)

        with input_list.open("w", encoding="utf-8") as f:
            f.write(str(raw_input))

        return {
            "raw_input": raw_input,
            "input_list": input_list,
        }

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