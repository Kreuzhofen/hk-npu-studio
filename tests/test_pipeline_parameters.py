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


if __name__ == "__main__":
    unittest.main()
