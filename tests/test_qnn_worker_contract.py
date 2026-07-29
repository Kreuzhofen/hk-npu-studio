from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from app.i18n import set_language
from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel
from engine.controlnet_canny_backend import ControlNetCannyQnnBackend
from engine.sd15_qnn_backend import StableDiffusion15QnnBackend
from engine.sd21_qnn_backend import StableDiffusion21QnnBackend


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
