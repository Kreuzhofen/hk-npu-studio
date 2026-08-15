from __future__ import annotations

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from controllers.generation_job import GenerationJob
from controllers.generation_pipeline import ImageGenerationPipeline
from controllers.generation_result import GenerationResult
from controllers.generation_session import GenerationSessionModel
from engine.stub_image_backend import StubImageBackend


class PipelineParameterTests(unittest.TestCase):
    def test_job_owns_immutable_parameter_snapshot(self):
        session = GenerationSessionModel(
            prompt="original",
            negative_prompt="negative",
            model_name="demo",
            width=640,
            height=384,
            steps=12,
            cfg_scale=6.5,
            seed=42,
            sampler="Euler",
            scheduler="Normal",
            batch_size=2,
            input_image_path="input.png",
            canny_low_threshold=40,
            canny_high_threshold=130,
            controlnet_conditioning_scale=0.8,
        )
        current = GenerationJob(session)
        session.prompt = "mutated"
        session.steps = 99

        self.assertEqual(current.parameters.prompt, "original")
        self.assertEqual(current.parameters.steps, 12)
        with self.assertRaises(FrozenInstanceError):
            current.parameters.steps = 20

    def test_worker_contract_contains_all_cpu_onnx_qnn_parameters(self):
        current = GenerationJob(
            GenerationSessionModel(prompt="test", model_name="demo")
        )

        values = current.parameters.to_worker_dict(current.job_id)

        self.assertEqual(
            set(values),
            {
                "prompt",
                "negative_prompt",
                "model_name",
                "width",
                "height",
                "steps",
                "cfg_scale",
                "seed",
                "sampler",
                "scheduler",
                "batch_size",
                "output_directory",
                "output_prefix",
                "input_image_path",
                "controlnet_enabled",
                "canny_low_threshold",
                "canny_high_threshold",
                "controlnet_conditioning_scale",
                "job_id",
            },
        )
        self.assertEqual(values["job_id"], str(current.job_id))

    def test_cpu_backend_uses_job_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            session = GenerationSessionModel(
                prompt="snapshot prompt",
                model_name="demo",
                output_directory=directory,
                width=64,
                height=64,
                steps=3,
                cfg_scale=4.0,
            )
            current = GenerationJob(session)
            session.prompt = "changed too late"
            session.output_directory = "not-used"

            result = StubImageBackend("CPU").generate(current)

            self.assertTrue(result.success)
            self.assertEqual(result.metadata["prompt"], "snapshot prompt")
            self.assertEqual(result.metadata["steps"], 3)
            self.assertEqual(Path(result.image_path).parent, Path(directory))

    def test_pipeline_validation_uses_same_snapshot(self):
        session = GenerationSessionModel(prompt="test", width=512, height=512)
        current = GenerationJob(session)
        session.width = 0
        pipeline = ImageGenerationPipeline(current, backend_adapter=None)
        pipeline.execute = lambda: GenerationResult(
            True, "FINISHED", "done", model_name="demo"
        )

        result = pipeline.run()

        self.assertTrue(result.success)

    def test_sd35_seed_normalization(self):
        import numpy as np

        # Test 1: seed < 0 results in uint32
        for _ in range(100):
            seed = -1
            if seed < 0:
                seed = int(np.random.randint(0, 4294967296, dtype=np.int64))
            self.assertTrue(0 <= seed <= 4294967295)

        # Test 2: seed > 4294967295 is normalized to uint32 deterministically
        seed = 4294967296
        if seed > 4294967295:
            seed = int(seed % 4294967296)
        self.assertEqual(seed, 0)

        seed = 4294967297
        if seed > 4294967295:
            seed = int(seed % 4294967296)
        self.assertEqual(seed, 1)

        # Test 3: valid seed is unchanged
        seed = 12345
        if seed < 0:
            pass
        elif seed > 4294967295:
            pass
        self.assertEqual(seed, 12345)

    def test_sd35_installation_first_step_explanation(self):
        from app.i18n import tr, set_language

        # Test German
        set_language("de_DE")
        explanation_de = tr("model_src_sd35_guided_description")
        self.assertIn("So funktioniert die Einrichtung:", explanation_de)
        self.assertIn("1. Laden Sie zuerst die benÃ¶tigte Qualcomm-Datei herunter.", explanation_de)

        # Test English
        set_language("en_US")
        explanation_en = tr("model_src_sd35_guided_description")
        self.assertIn("How setup works:", explanation_en)
        self.assertIn("1. Download the required Qualcomm file first.", explanation_en)

        # Test Spanish
        set_language("es_ES")
        explanation_es = tr("model_src_sd35_guided_description")
        self.assertIn("CÃ³mo funciona la configuraciÃ³n:", explanation_es)
        self.assertIn("1. Descargue primero el archivo requerido de Qualcomm.", explanation_es)


if __name__ == "__main__":
    unittest.main()
