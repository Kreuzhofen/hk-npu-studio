from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import atexit
import secrets
import socket
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse
from engine.inference_backend import InferenceBackend
from engine.job_lifecycle import cancel_job
from engine.logging_config import get_logger


logger = get_logger("StableDiffusion15QaiAppBuilderBackend")
BACKEND_NAME = "Qualcomm SD1.5 QAI AppBuilder (HTP)"
MODEL_ID = "stable_diffusion_v1_5_qnn"
_MODEL_FILES = (
    "stable_diffusion_v1_5_w8a16_quantized-textencoderquantizable-qualcomm_snapdragon_x_elite.bin",
    "stable_diffusion_v1_5_w8a16_quantized-unetquantizable-qualcomm_snapdragon_x_elite.bin",
    "stable_diffusion_v1_5_w8a16_quantized-vaedecoderquantizable-qualcomm_snapdragon_x_elite.bin",
)


def _qai_root() -> Path:
    configured = os.environ.get("SNAPDRAGON_QAI_APPBUILDER_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2] / "QAI-AppBuilder-Test"


def _worker_python() -> Path:
    configured = os.environ.get("SNAPDRAGON_QAI_APPBUILDER_PYTHON", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return _qai_root() / ".venv" / "Scripts" / "python.exe"


def _model_dir() -> Path:
    configured = os.environ.get("SNAPDRAGON_QAI_SD15_MODEL_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "models" / "stable_diffusion_v1_5_qai"
    return (
        _qai_root()
        / "samples"
        / "GenerativeAI"
        / "Image_Generation"
        / "stable_diffusion_v1_5"
        / "models"
    )


class StableDiffusion15QaiAppBuilderBackend(InferenceBackend):
    """Persistent, process-isolated QAI AppBuilder prototype for SD1.5."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._channel: socket.socket | None = None
        self._reader: Any = None
        self._writer: Any = None
        self._lock = threading.RLock()
        self._generation_lock = threading.Lock()

    def get_backend_name(self) -> str:
        return BACKEND_NAME

    def get_backend_version(self) -> str:
        return "prototype"

    def get_supported_models(self) -> list[str]:
        return [MODEL_ID]

    def is_available(self) -> bool:
        python = _worker_python()
        model_dir = _model_dir()
        if not python.is_file() or not all((model_dir / name).is_file() for name in _MODEL_FILES):
            return False
        probe = (
            "from qai_appbuilder import QNNConfig,QNNContext,Runtime,LogLevel,ProfilingLevel; "
            "QNNConfig.Config(Runtime.HTP,LogLevel.ERROR,ProfilingLevel.BASIC)"
        )
        try:
            if getattr(sys, "frozen", False):
                command = [str(python), "--qai-appbuilder-probe"]
            else:
                command = [str(python), "-c", probe]
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return completed.returncode == 0

    def initialize(self) -> None:
        if not self.is_available():
            raise RuntimeError("QAI AppBuilder SD1.5 runtime or model contexts are unavailable")
        with self._lock:
            self._ensure_worker()

    def _ensure_worker(self) -> subprocess.Popen[str]:
        process = self._process
        if process is not None and process.poll() is None:
            return process
        if not self.is_available():
            raise RuntimeError("QAI AppBuilder SD1.5 backend is unavailable")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(30)
        host, port = listener.getsockname()
        token = secrets.token_hex(24)
        if getattr(sys, "frozen", False):
            command = [
                str(_worker_python()),
                "--qai-appbuilder-worker",
                host,
                str(port),
                token,
            ]
            worker_cwd = Path(sys.executable).resolve().parent
        else:
            command = [
                str(_worker_python()),
                str(Path(__file__).resolve()),
                "--worker",
                host,
                str(port),
                token,
            ]
            worker_cwd = _qai_root()
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                cwd=str(worker_cwd),
            )
            self._process = process
            channel, _ = listener.accept()
        finally:
            listener.close()
        self._channel = channel
        self._reader = channel.makefile("r", encoding="utf-8")
        self._writer = channel.makefile("w", encoding="utf-8")
        response = self._read_response(process)
        if response.get("token") != token:
            self._stop_worker()
            raise RuntimeError("QAI worker authentication failed")
        if not response.get("ok") or response.get("event") != "ready":
            self._stop_worker()
            raise RuntimeError(response.get("error", "QAI worker failed during initialization"))
        return process

    def _read_response(self, process: subprocess.Popen[str]) -> dict[str, Any]:
        if self._reader is None:
            raise RuntimeError("QAI worker channel is unavailable")
        while True:
            line = self._reader.readline()
            if not line:
                raise RuntimeError("QAI worker exited without a response")
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    def generate(self, job: GenerationJob) -> GenerationResponse:
        if job.cancel_requested.is_set():
            return GenerationResponse(
                success=False,
                status="CANCELLED",
                message="Generation cancelled",
                model_name=job.parameters.model_name,
            )
        with self._generation_lock:
            try:
                with self._lock:
                    process = self._ensure_worker()
                    if self._writer is None:
                        raise RuntimeError("QAI worker channel is unavailable")
                    self._writer.write(
                        json.dumps(
                            {"command": "generate", "job": job.parameters.to_worker_dict(job.job_id)},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    self._writer.flush()
                result = self._read_response(process)
            except Exception as error:
                with self._lock:
                    self._stop_worker()
                if job.cancel_requested.is_set():
                    return GenerationResponse(
                        success=False,
                        status="CANCELLED",
                        message="Generation cancelled",
                        model_name=job.parameters.model_name,
                    )
                logger.error("QAI AppBuilder worker failed: %s", error)
                return GenerationResponse(
                    success=False,
                    status="PipelineError",
                    message=str(error),
                    model_name=job.parameters.model_name,
                )

        if not result.get("ok"):
            return GenerationResponse(
                success=False,
                status="PipelineError",
                message=str(result.get("error", "QAI generation failed")),
                model_name=job.parameters.model_name,
            )
        image_path = str(result["image_path"])
        return GenerationResponse(
            success=True,
            status="FINISHED",
            message="QAI AppBuilder SD1.5 generation completed",
            image_path=image_path,
            thumbnail_path=image_path,
            generation_time=float(result["generation_time"]),
            backend_name=BACKEND_NAME,
            model_name=job.parameters.model_name,
            metadata={
                "backend": BACKEND_NAME,
                "worker_pid": result.get("worker_pid"),
                "persistent_worker": True,
                "steps": job.parameters.steps,
                "cfg": job.parameters.cfg_scale,
                "seed": result.get("seed"),
            },
        )

    def cancel(self, job: GenerationJob) -> str:
        cancel_job(job)
        with self._lock:
            self._stop_worker()
        return "Generation cancelled"

    def shutdown(self) -> None:
        """Per-job factory cleanup hook; the shared worker intentionally stays alive."""

    def close(self) -> None:
        """Final application-level shutdown of the persistent worker."""
        with self._lock:
            process = self._process
            if process is not None and process.poll() is None and self._writer is not None:
                try:
                    self._writer.write('{"command":"shutdown"}\n')
                    self._writer.flush()
                    process.wait(timeout=10)
                except (OSError, subprocess.SubprocessError):
                    pass
            self._stop_worker()

    def _stop_worker(self) -> None:
        process = self._process
        self._process = None
        for stream_name in ("_reader", "_writer"):
            stream = getattr(self, stream_name)
            setattr(self, stream_name, None)
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass
        channel = self._channel
        self._channel = None
        if channel is not None:
            try:
                channel.close()
            except OSError:
                pass
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def _worker_main() -> int:
    import gc

    worker_flag = "--qai-appbuilder-worker" if getattr(sys, "frozen", False) else "--worker"
    flag_index = sys.argv.index(worker_flag)
    host = sys.argv[flag_index + 1]
    port = int(sys.argv[flag_index + 2])
    token = sys.argv[flag_index + 3]
    channel = socket.create_connection((host, port), timeout=30)
    reader = channel.makefile("r", encoding="utf-8")
    writer = channel.makefile("w", encoding="utf-8")

    try:
        import numpy as np
        from PIL import Image
        from qai_appbuilder import PerfProfile
    except Exception as exc:
        writer.write(
            json.dumps(
                {"ok": False, "event": "ready", "token": token, "error": str(exc)}
            )
            + "\n"
        )
        writer.flush()
        return 1

    if getattr(sys, "frozen", False):
        common_dir = Path(sys.executable).resolve().parent / "qai_appbuilder_common"
    else:
        common_dir = _qai_root() / "samples" / "common"
    sys.path.insert(0, str(common_dir))
    try:
        from _stable_diffusion import (  # type: ignore[import-not-found]
            TextEncoderBase,
            UnetBase,
            VaeDecoderBase,
            decode_vae_output,
            generate_initial_latent,
            get_timestep,
            load_tokenizer,
            make_scheduler,
            run_scheduler,
            run_tokenizer,
            set_qnn_config,
        )
    except Exception as exc:
        writer.write(
            json.dumps(
                {"ok": False, "event": "ready", "token": token, "error": str(exc)}
            )
            + "\n"
        )
        writer.flush()
        return 1

    class TextEncoder(TextEncoderBase):
        _embed_dim = 768

    class Unet(UnetBase):
        pass

    class VaeDecoder(VaeDecoderBase):
        pass

    model_dir = _model_dir()
    tokenizer = text_encoder = unet = vae_decoder = scheduler = None
    try:
        set_qnn_config()
        tokenizer = load_tokenizer(
            "openai/clip-vit-large-patch14",
            model_dir / "tokenizer",
            "Local Qualcomm SD1.5 tokenizer is required",
            use_subfolder=False,
        )
        text_encoder = TextEncoder("text_encoder", str(model_dir / _MODEL_FILES[0]))
        unet = Unet("model_unet", str(model_dir / _MODEL_FILES[1]))
        vae_decoder = VaeDecoder("vae_decoder", str(model_dir / _MODEL_FILES[2]))
        scheduler = make_scheduler()
        PerfProfile.SetPerfProfileGlobal(PerfProfile.BURST)
        writer.write(
            json.dumps(
                {"ok": True, "event": "ready", "worker_pid": os.getpid(), "token": token}
            )
            + "\n"
        )
        writer.flush()

        for line in reader:
            request = json.loads(line)
            if request.get("command") == "shutdown":
                break
            if request.get("command") != "generate":
                writer.write(json.dumps({"ok": False, "error": "Unknown worker command"}) + "\n")
                writer.flush()
                continue
            try:
                job = request["job"]
                if int(job.get("width", 512)) != 512 or int(job.get("height", 512)) != 512:
                    raise ValueError("QAI SD1.5 prototype supports only 512x512")
                steps = int(job.get("steps", 20))
                guidance = float(job.get("cfg_scale", 7.5))
                seed = int(job.get("seed", -1))
                if seed < 0:
                    seed = int(np.random.randint(0, 9_999_999_999, dtype=np.int64))
                scheduler.set_timesteps(steps)
                start = time.perf_counter()
                cond_tokens = run_tokenizer(tokenizer, str(job.get("prompt", "")), 77)
                uncond_tokens = run_tokenizer(tokenizer, str(job.get("negative_prompt", "")), 77)
                uncond_embedding = text_encoder.Inference(uncond_tokens)
                cond_embedding = text_encoder.Inference(cond_tokens)
                latent = generate_initial_latent(seed=np.int64(seed))
                for index in range(steps):
                    timestep = get_timestep(scheduler, index)
                    noise_uncond = unet.Inference(latent, timestep, uncond_embedding)
                    noise_cond = unet.Inference(latent, timestep, cond_embedding)
                    latent = run_scheduler(
                        scheduler,
                        noise_uncond,
                        noise_cond,
                        latent,
                        timestep,
                        guidance,
                    )
                output_raw = vae_decoder.Inference(latent)
                generation_time = time.perf_counter() - start
                if len(output_raw) == 0:
                    raise RuntimeError("VAE returned no image data")
                image: Image.Image = decode_vae_output(output_raw)
                output_dir = Path(str(job.get("output_directory", "output"))).resolve()
                output_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{job.get('output_prefix', 'generate')}_{str(job.get('job_id', ''))[:8]}.png"
                image_path = output_dir / filename
                image.save(image_path, format="PNG")
                writer.write(
                    json.dumps(
                        {
                            "ok": True,
                            "image_path": str(image_path),
                            "generation_time": generation_time,
                            "worker_pid": os.getpid(),
                            "seed": seed,
                        }
                    )
                    + "\n"
                )
                writer.flush()
            except Exception as error:
                writer.write(json.dumps({"ok": False, "error": str(error)}) + "\n")
                writer.flush()
    except Exception as exc:
        writer.write(
            json.dumps(
                {"ok": False, "event": "ready", "token": token, "error": str(exc)}
            )
            + "\n"
        )
        writer.flush()
        return 1
    finally:
        try:
            PerfProfile.RelPerfProfileGlobal()
        except Exception:
            pass
        for context in (vae_decoder, unet, text_encoder):
            if context is not None:
                try:
                    context.release()
                except Exception:
                    pass
        del scheduler, vae_decoder, unet, text_encoder, tokenizer
        gc.collect()
        reader.close()
        writer.close()
        channel.close()
    return 0


def worker_probe_main() -> int:
    try:
        from qai_appbuilder import LogLevel, ProfilingLevel, QNNConfig, Runtime

        QNNConfig.Config(Runtime.HTP, LogLevel.ERROR, ProfilingLevel.BASIC)
        return 0
    except Exception:
        return 1


_SHARED_BACKEND: StableDiffusion15QaiAppBuilderBackend | None = None
_SHARED_BACKEND_LOCK = threading.Lock()


def get_shared_backend() -> StableDiffusion15QaiAppBuilderBackend:
    global _SHARED_BACKEND
    with _SHARED_BACKEND_LOCK:
        if _SHARED_BACKEND is None:
            _SHARED_BACKEND = StableDiffusion15QaiAppBuilderBackend()
            atexit.register(_SHARED_BACKEND.close)
        return _SHARED_BACKEND


if __name__ == "__main__" and "--worker" in sys.argv:
    raise SystemExit(_worker_main())
