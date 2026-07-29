from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from controllers.generation_job import GenerationJob
from controllers.generation_pipeline import ImageGenerationPipeline
from controllers.generation_result import GenerationResult
from controllers.generation_session import GenerationSessionModel
from engine.generation_executor import GenerationExecutor
from engine.generation_response import GenerationResponse
from engine.job_lifecycle import JobStatus
from engine.runtime_model import RuntimeModel


def job(**session_values) -> GenerationJob:
    values = {"prompt": "test", "model_name": "demo"}
    values.update(session_values)
    return GenerationJob(session=GenerationSessionModel(**values))


class InferencePipelineContractTests(unittest.TestCase):
    def test_invalid_input_is_forwarded_to_job_engine(self):
        current = job(width=0)
        pipeline = ImageGenerationPipeline(current, backend_adapter=None)
        pipeline.execute = MagicMock()

        result = pipeline.run()

        self.assertFalse(result.success)
        self.assertEqual(result.status, "ValidationError")
        self.assertEqual(current.status, JobStatus.FAILED.value)
        self.assertIn("invalid parameters", current.error_message)
        pipeline.execute.assert_not_called()

    def test_pre_cancelled_job_never_reaches_backend(self):
        current = job()
        current.cancel()
        pipeline = ImageGenerationPipeline(current, backend_adapter=None)
        pipeline.execute = MagicMock()

        result = pipeline.run()

        self.assertFalse(result.success)
        self.assertEqual(result.status, JobStatus.CANCELLED.value)
        self.assertEqual(current.status, JobStatus.CANCELLED.value)
        pipeline.execute.assert_not_called()

    def test_cancel_during_execution_overrides_backend_success(self):
        current = job()
        pipeline = ImageGenerationPipeline(current, backend_adapter=None)

        def execute():
            current.cancel()
            return GenerationResult(True, "SUCCESS", "late success")

        pipeline.execute = execute
        result = pipeline.run()

        self.assertFalse(result.success)
        self.assertEqual(result.status, JobStatus.CANCELLED.value)
        self.assertEqual(current.status, JobStatus.CANCELLED.value)

    def test_success_result_is_normalized(self):
        current = job()
        pipeline = ImageGenerationPipeline(current, backend_adapter=None)
        pipeline.execute = MagicMock(
            return_value=GenerationResult(
                True, "SUCCESS", "done", model_name="", metadata=None
            )
        )

        result = pipeline.run()

        self.assertEqual(result.status, JobStatus.FINISHED.value)
        self.assertEqual(result.model_name, "demo")
        self.assertEqual(result.metadata, {})
        self.assertEqual(current.status, JobStatus.FINISHED.value)

    def test_invalid_backend_result_fails_job_and_cleans_up(self):
        current = job()

        class TrackingPipeline(ImageGenerationPipeline):
            cleaned = False

            def cleanup(self):
                self.cleaned = True

        pipeline = TrackingPipeline(current, backend_adapter=None)
        pipeline.execute = MagicMock(return_value=None)

        result = pipeline.run()

        self.assertFalse(result.success)
        self.assertEqual(result.status, "PipelineError")
        self.assertEqual(current.status, JobStatus.FAILED.value)
        self.assertTrue(pipeline.cleaned)
        self.assertIn("GenerationResult", current.error_message)

    def test_executor_reuses_preloaded_runtime_without_second_load(self):
        current = job()
        runtime = RuntimeModel(
            model_id="demo",
            model_path="C:/models/demo",
            files=[],
            backend="CPU",
            load_plan=None,
        )
        executor = GenerationExecutor.__new__(GenerationExecutor)
        executor.loader_service = MagicMock()
        response = GenerationResponse(
            True, JobStatus.FINISHED.value, "done", model_name="demo"
        )
        backend = MagicMock()
        backend.get_backend_name.return_value = "CPU (Stub)"

        with patch(
            "engine.generation_executor.LocalImageGeneratorAdapter.generate",
            return_value=response,
        ):
            result = executor.execute(
                current, backend_adapter=backend, runtime_model=runtime
            )

        self.assertIs(result, response)
        executor.loader_service.load_model.assert_not_called()
        executor.loader_service.unload_model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
