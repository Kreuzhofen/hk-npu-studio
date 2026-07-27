from __future__ import annotations

from io import StringIO
from pathlib import Path
import tempfile
from threading import Event, Thread
import unittest
from unittest.mock import patch

import numpy as np

from controllers.generation_job import GenerationJob
from controllers.generation_controller import GenerationController
from controllers.generation_result import GenerationResult
from controllers.generation_session import GenerationSessionModel
from engine.backends.sd15_qnn_backend_adapter import StableDiffusion15QnnBackendAdapter
from engine.backends.sd21_qnn_backend_adapter import StableDiffusion21QnnBackendAdapter
from engine.backends.controlnet_canny_backend_adapter import ControlNetCannyQnnBackendAdapter
from engine.generation_response import GenerationResponse
from engine.local_image_generator_adapter import LocalImageGeneratorAdapter
import engine.sd15_qnn_backend as sd15
import engine.sd21_qnn_backend as sd21
import engine.controlnet_canny_backend as controlnet_canny


SD15_MODEL_DIR = Path(
    r"C:\SnapdragonAI\temp\stable_diffusion_v1_5_qnn_inspection\stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite"
)
SD21_MODEL_DIR = Path(r"C:\SnapdragonAI\models\stable_diffusion_v2_1")


class _FakeProcess:
    def __init__(self) -> None:
        self.stdout = StringIO("Step 1/20: test\n")
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = -15 if self.terminated else 0
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9


class _FakeSession:
    def __init__(self) -> None:
        self.finalized = 0

    def end_profiling(self) -> str:
        self.finalized += 1
        return "profile.json"


class ProductionQnnPipelineTests(unittest.TestCase):
    def test_clip_prompt_normalization_matches_reference_cleaning(self) -> None:
        cases = (
            (sd15.SimpleCLIPTokenizer, SD15_MODEL_DIR),
            (sd21.SimpleCLIPTokenizer, SD21_MODEL_DIR),
        )
        for tokenizer_type, model_dir in cases:
            tokenizer = tokenizer_type(model_dir / "tokenizer" / "vocab.json", model_dir / "tokenizer" / "merges.txt")
            self.assertEqual(tokenizer.encode("fish & chips"), tokenizer.encode("fish &amp; chips"))
            self.assertEqual(tokenizer.encode("café"), tokenizer.encode("CAFÉ"))

    def test_tokenizer_padding_matches_each_package_contract(self) -> None:
        sd15_tokenizer = sd15.SimpleCLIPTokenizer(
            SD15_MODEL_DIR / "tokenizer" / "vocab.json", SD15_MODEL_DIR / "tokenizer" / "merges.txt"
        )
        sd21_tokenizer = sd21.SimpleCLIPTokenizer(
            SD21_MODEL_DIR / "tokenizer" / "vocab.json", SD21_MODEL_DIR / "tokenizer" / "merges.txt"
        )
        self.assertEqual(49407, sd15_tokenizer.tokenize_prompt("test")[-1])
        self.assertEqual(0, sd21_tokenizer.tokenize_prompt("test")[-1])

    def test_scheduler_contracts_match_package_reference(self) -> None:
        euler = sd15.EulerScheduler()
        euler.set_timesteps(20)
        np.testing.assert_array_equal(euler.timesteps, np.arange(951, 0, -50, dtype=np.int32))
        self.assertEqual(0.0, float(euler.sigmas[-1]))
        self.assertTrue(np.all(np.diff(euler.sigmas) < 0.0))

        ddim = sd21.StableDiffusion21DDIMScheduler()
        ddim.set_timesteps(20)
        np.testing.assert_array_equal(ddim.timesteps, np.arange(951, 0, -50, dtype=np.int32))
        sample = np.full((1, 2, 2, 1), 0.25, dtype=np.float32)
        velocity = np.full_like(sample, -0.5)
        actual = ddim.step(velocity, 951, sample, 50)
        alpha_t = ddim.alphas_cumprod[951]
        alpha_previous = ddim.alphas_cumprod[901]
        beta_t = 1.0 - alpha_t
        predicted_original = alpha_t**0.5 * sample - beta_t**0.5 * velocity
        predicted_epsilon = alpha_t**0.5 * velocity + beta_t**0.5 * sample
        expected = alpha_previous**0.5 * predicted_original + (1.0 - alpha_previous) ** 0.5 * predicted_epsilon
        np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)

    def test_cancel_terminates_qnn_worker(self) -> None:
        for backend in (sd15.StableDiffusion15QnnBackend(), sd21.StableDiffusion21QnnBackend(), controlnet_canny.ControlNetCannyQnnBackend()):
            session = GenerationSessionModel()
            if isinstance(backend, sd15.StableDiffusion15QnnBackend):
                session.model_name = "stable_diffusion_v1_5_qnn"
            elif isinstance(backend, sd21.StableDiffusion21QnnBackend):
                session.model_name = "stable_diffusion_v2_1_qnn"
            else:
                session.model_name = "controlnet_canny_qnn"
            job = GenerationJob(session=session, status="RUNNING")
            process = _FakeProcess()
            backend._active_process = process

            response = backend.cancel(job)

            self.assertTrue(process.terminated)
            self.assertTrue(job.cancel_requested.is_set())
            self.assertEqual("CANCELLED", job.status)
            self.assertEqual("CANCELLED", response)

    def test_cancel_reaches_physical_backend_through_local_adapter(self) -> None:
        for adapter in (StableDiffusion15QnnBackendAdapter(), StableDiffusion21QnnBackendAdapter(), ControlNetCannyQnnBackendAdapter()):
            entered = Event()
            released = Event()

            class _PhysicalBackend:
                cancel_called = False

                def generate(self, job: GenerationJob) -> GenerationResponse:
                    entered.set()
                    released.wait(timeout=2)
                    return GenerationResponse(
                        success=False,
                        status="CANCELLED",
                        message="Generation cancelled.",
                        model_name=job.session.model_name,
                    )

                def cancel(self, job: GenerationJob) -> str:
                    self.cancel_called = True
                    released.set()
                    return "CANCELLED"

            physical = _PhysicalBackend()
            session = GenerationSessionModel()
            job = GenerationJob(session=session, status="RUNNING")
            local = LocalImageGeneratorAdapter(adapter)
            response: list[GenerationResponse] = []

            with patch("engine.inference_backend_factory.InferenceBackendFactory.get_backend", return_value=physical):
                worker = Thread(target=lambda: response.append(local.generate(job)))
                worker.start()
                self.assertTrue(entered.wait(timeout=2))
                adapter.cancel(job)
                worker.join(timeout=2)

            self.assertFalse(worker.is_alive())
            self.assertTrue(physical.cancel_called)
            self.assertTrue(job.cancel_requested.is_set())
            self.assertEqual("CANCELLED", response[0].status)

    def test_cancelled_output_and_sidecar_are_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = GenerationSessionModel(output_directory=directory, model_name="test_model")
            job = GenerationJob(session=session, status="CANCELLED")
            image_path = Path(directory) / f"cancelled_{str(job.job_id)[:8]}.png"
            sidecar_path = image_path.with_suffix(".json")
            image_path.write_bytes(b"late image")
            sidecar_path.write_text("{}", encoding="utf-8")
            result = GenerationResult(
                success=True,
                status="FINISHED",
                message="late result",
                image_path=str(image_path),
                thumbnail_path=str(image_path),
            )

            cancelled = GenerationController.discard_cancelled_output(result, job)

            self.assertFalse(image_path.exists())
            self.assertFalse(sidecar_path.exists())
            self.assertFalse(cancelled.success)
            self.assertEqual("CANCELLED", cancelled.status)

    def test_sessions_are_finalized_after_pipeline_error(self) -> None:
        cases = (
            (sd15, sd15.StableDiffusion15QnnBackend(), "stable_diffusion_v1_5_qnn", 3),
            (sd21, sd21.StableDiffusion21QnnBackend(), "stable_diffusion_v2_1_qnn", 3),
            (controlnet_canny, controlnet_canny.ControlNetCannyQnnBackend(), "controlnet_canny_qnn", 4),
        )
        real_image = r"C:\SnapdragonAI\output\generate_1784201535_01a65e09.png"
        for module, backend, model_name, expected_sessions_count in cases:
            sessions = [_FakeSession() for _ in range(expected_sessions_count)]
            with patch.object(backend, "_setup_sessions", return_value=(*sessions, {})), patch.object(
                module, "SimpleCLIPTokenizer", side_effect=RuntimeError("injected tokenizer failure")
            ), patch("pathlib.Path.exists", return_value=True):
                result = backend._execute_generation_physical({"model_name": model_name, "input_image_path": real_image})
            self.assertFalse(result["success"])
            self.assertEqual([1] * expected_sessions_count, [session.finalized for session in sessions])


if __name__ == "__main__":
    unittest.main()
