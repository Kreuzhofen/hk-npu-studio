from __future__ import annotations

import json
import os
from io import StringIO
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

import numpy as np

from app.i18n import set_language
from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.controlnet_canny_backend import ControlNetCannyQnnBackend
from engine.sd15_qnn_backend import StableDiffusion15QnnBackend
from engine.sd21_qnn_backend import StableDiffusion21QnnBackend
import engine.controlnet_canny_backend as controlnet_canny
import engine.sd15_qnn_backend as sd15
import engine.sd21_qnn_backend as sd21


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKERS = (
    PROJECT_ROOT / "engine" / "sd15_qnn_backend.py",
    PROJECT_ROOT / "engine" / "sd21_qnn_backend.py",
    PROJECT_ROOT / "engine" / "controlnet_canny_backend.py",
)


class _EmptyWorkerProcess:
    def __init__(self) -> None:
        self.stdout = StringIO("")
        self.returncode = 1

    def poll(self) -> int:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        return self.returncode


class QnnWorkerContractTests(unittest.TestCase):
    def test_sd15_and_controlnet_have_no_fixed_global_python_path(self) -> None:
        for backend in (sd15, controlnet_canny):
            source = Path(backend.__file__).read_text(encoding="utf-8")
            self.assertNotIn(r"C:\Program Files\Python311-arm64", source)
            self.assertNotIn("C:/Program Files/Python311-arm64", source)

    def test_sd15_and_controlnet_worker_resolvers_prefer_environment_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            interpreter = Path(directory) / "python.exe"
            interpreter.touch()
            with patch.dict(os.environ, {"SNAPDRAGON_QNN_PYTHON": str(interpreter)}):
                self.assertEqual(str(interpreter), sd15._resolve_worker_python())
                self.assertEqual(str(interpreter), controlnet_canny._resolve_worker_python())

    def test_sd21_png_export_has_no_pillow_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "worker.png"
            image = np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8)
            with patch.dict(sys.modules, {"PIL": None}):
                sd21._write_rgb_png(output, image)

            data = output.read_bytes()
            self.assertEqual(b"\x89PNG\r\n\x1a\n", data[:8])
            self.assertEqual((2, 1), struct.unpack(">II", data[16:24]))
            idat_length = struct.unpack(">I", data[33:37])[0]
            self.assertEqual(b"IDAT", data[37:41])
            self.assertEqual(b"\x00" + image.tobytes(), zlib.decompress(data[41:41 + idat_length]))

    def test_sd21_model_fallback_uses_installed_package_directory(self) -> None:
        self.assertEqual(sd21.MODELS_DIR / "stable_diffusion_v2_1_qnn", sd21.MODEL_DIR)

    def test_sd21_successful_worker_output_maps_to_finished_response_and_cleans_ipc(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_path = root / "generated.png"
            image_path.write_bytes(b"png")

            class SuccessfulWorkerProcess:
                returncode = 0

                def __init__(self, command, **_kwargs) -> None:
                    self.stdout = StringIO("")
                    output_path = Path(command[-1])
                    output_path.write_text(
                        json.dumps({
                            "success": True,
                            "message": "complete",
                            "image_path": str(image_path),
                            "generation_time": 1.25,
                            "metadata": {"worker": "sd21"},
                        }),
                        encoding="utf-8",
                    )

                def poll(self) -> int:
                    return self.returncode

                def wait(self, timeout: float | None = None) -> int:
                    return self.returncode

            backend = StableDiffusion21QnnBackend()
            job = GenerationJob(GenerationSessionModel(model_name="stable_diffusion_v2_1_qnn"))
            with patch.object(sd21, "ROOT", root), patch.object(
                sd21, "_resolve_worker_python", return_value=sys.executable
            ), patch.object(sd21, "_qnn_package_dir_for_worker", return_value=None), patch(
                "subprocess.Popen", side_effect=SuccessfulWorkerProcess
            ) as popen:
                response = backend.generate(job)

            command = popen.call_args.args[0]
            self.assertEqual([sys.executable, str(Path(sd21.__file__).resolve())], command[:2])
            self.assertTrue(response.success)
            self.assertEqual("FINISHED", response.status)
            self.assertEqual(str(image_path), response.image_path)
            self.assertEqual({"worker": "sd21"}, response.metadata)
            self.assertFalse(Path(command[-2]).exists())
            self.assertFalse(Path(command[-1]).exists())

    def test_direct_workers_import_project_and_write_failure_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            for index, worker in enumerate(WORKERS):
                output_path = temp_dir / f"output-{index}.json"
                result = subprocess.run(
                    [sys.executable, str(worker), str(temp_dir / "missing.json"), str(output_path)],
                    cwd=temp_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(1, result.returncode, result.stderr)
                payload = json.loads(output_path.read_text(encoding="utf-8"))
                self.assertIs(payload["success"], False)
                self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_missing_worker_json_returns_localized_public_error(self) -> None:
        cases = (
            (StableDiffusion15QnnBackend(), "stable_diffusion_v1_5_qnn"),
            (StableDiffusion21QnnBackend(), "stable_diffusion_v2_1_qnn"),
            (ControlNetCannyQnnBackend(), "controlnet_canny_qnn"),
        )
        translations = {
            "de_DE": "Die Generierung konnte nicht abgeschlossen werden. Details wurden protokolliert.",
            "en_US": "The generation could not be completed. Details were written to the log.",
            "es_ES": "No se pudo completar la generación. Los detalles se guardaron en el registro.",
        }
        try:
            for language, expected in translations.items():
                set_language(language)
                for backend, model_name in cases:
                    session = GenerationSessionModel(model_name=model_name)
                    with patch("subprocess.Popen", return_value=_EmptyWorkerProcess()):
                        response = backend.generate(GenerationJob(session=session))
                    self.assertFalse(response.success)
                    self.assertEqual(expected, response.message)
                    self.assertNotIn("Subprocess", response.message)
        finally:
            set_language("de_DE")


if __name__ == "__main__":
    unittest.main()
