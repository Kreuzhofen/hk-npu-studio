"""
SnapdragonAI Studio

QNN Backend

Created by Holger Kreuzhofen
Phoenix Engine
"""

from pathlib import Path
import os
import subprocess

import numpy as np
from PIL import Image


class QNNBackend:
    """
    Backend für Qualcomm AI Engine (QNN).

    Diese Klasse kapselt sämtliche Kommunikation
    mit qnn-net-run und den QNN-Modellen.
    """

    def __init__(self):
        self.base_path = Path(r"C:\SnapdragonAI")
        self.input_dir = self.base_path / "input"
        self.output_dir = self.base_path / "output"

        self.qnn_bin = Path(
            r"C:\Qualcomm\AIStack\2.47.0.260601\bin\aarch64-windows-msvc\qnn-net-run.exe"
        )
        self.qnn_backend = Path(
            r"C:\Qualcomm\AIStack\2.47.0.260601\lib\aarch64-windows-msvc\QnnHtp.dll"
        )
        self.model_path = self.base_path / "models" / "real_esrgan_x4plus.bin"

        self.result_raw = self.output_dir / "Result_0" / "upscaled_image.raw"
        self.result_png = self.output_dir / "upscaled_image.png"

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

    def execute_qnn(self, input_list):
        """
        Startet qnn-net-run mit dem vorbereiteten input_list.txt.
        """

        self.output_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["PATH"] = (
            str(self.qnn_backend.parent)
            + ";"
            + str(self.qnn_bin.parent)
            + ";"
            + env["PATH"]
        )

        cmd = [
            str(self.qnn_bin),
            "--retrieve_context",
            str(self.model_path),
            "--backend",
            str(self.qnn_backend),
            "--input_list",
            str(input_list),
            "--output_dir",
            str(self.output_dir),
            "--log_level",
            "info",
        ]

        subprocess.run(cmd, env=env, check=True)

        return {
            "status": "qnn_executed",
            "output_dir": self.output_dir,
        }

    def read_output(self):
        """
        Liest die von qnn-net-run erzeugte RAW-Ausgabedatei ein.
        """

        if not self.result_raw.exists():
            raise FileNotFoundError(self.result_raw)

        output = np.fromfile(self.result_raw, dtype=np.float32)
        output = output.reshape(1, 512, 512, 3)

        return output

    def save_output(self, output):
        """
        Speichert den QNN-Ausgabetensor als PNG-Datei.
        """

        image = output[0]
        image = np.clip(image * 255, 0, 255).astype(np.uint8)

        Image.fromarray(image).save(self.result_png)

        return self.result_png

    def upscale(self, image_path):
        """
        Führt ein RealESRGAN-Upscaling über die QNN-Pipeline aus.
        """

        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(image_path)

        tensor = self.prepare_input(image_path)
        files = self.write_raw_input(tensor)

        self.execute_qnn(files["input_list"])

        output = self.read_output()
        result_png = self.save_output(output)

        return {
            "status": "success",
            "image": str(image_path),
            "output": str(result_png),
            "backend": "QNN"
        }