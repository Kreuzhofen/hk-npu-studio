from __future__ import annotations

import atexit
import gc
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config import MODELS_DIR
from engine.sd15_qai_appbuilder_backend import (
    StableDiffusion15QaiAppBuilderBackend,
    _qai_root,
    _worker_python,
)


BACKEND_NAME = "Qualcomm SD2.1 QAI AppBuilder (HTP)"
MODEL_ID = "stable_diffusion_v2_1_qai"
LEGACY_MODEL_ID = "stable_diffusion_v2_1_qnn"
_MODEL_FILES = (
    "stable_diffusion_v2_1_quantized-textencoderquantizable-qualcomm_snapdragon_x_elite.bin",
    "stable_diffusion_v2_1_quantized-unetquantizable-qualcomm_snapdragon_x_elite.bin",
    "stable_diffusion_v2_1_quantized-vaedecoderquantizable-qualcomm_snapdragon_x_elite.bin",
)


def _model_dir() -> Path:
    configured = os.environ.get("SNAPDRAGON_QAI_SD21_MODEL_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return MODELS_DIR / MODEL_ID


def _has_local_tokenizer(model_dir: Path) -> bool:
    tokenizer_dir = model_dir / "tokenizer"
    return (
        tokenizer_dir.is_dir()
        and any(tokenizer_dir.rglob("tokenizer_config.json"))
        and any(tokenizer_dir.rglob("vocab.json"))
        and any(tokenizer_dir.rglob("merges.txt"))
    )


class StableDiffusion21QaiAppBuilderBackend(StableDiffusion15QaiAppBuilderBackend):
    """Persistent, process-isolated QAI AppBuilder backend for SD2.1."""

    def get_backend_name(self) -> str:
        return BACKEND_NAME

    def get_supported_models(self) -> list[str]:
        return [MODEL_ID, LEGACY_MODEL_ID]

    def is_available(self) -> bool:
        python = _worker_python()
        model_dir = _model_dir()
        if (
            not python.is_file()
            or not all((model_dir / name).is_file() for name in _MODEL_FILES)
            or not _has_local_tokenizer(model_dir)
        ):
            return False
        probe = (
            "from qai_appbuilder import QNNConfig,QNNContext,Runtime,LogLevel,ProfilingLevel; "
            "QNNConfig.Config(Runtime.HTP,LogLevel.ERROR,ProfilingLevel.BASIC)"
        )
        try:
            command = (
                [str(python), "--qai-appbuilder-probe"]
                if getattr(sys, "frozen", False)
                else [str(python), "-c", probe]
            )
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=15, check=False
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return completed.returncode == 0

    def _ensure_worker(self) -> subprocess.Popen[str]:
        process = self._process
        if process is not None and process.poll() is None:
            return process
        if not self.is_available():
            raise RuntimeError("QAI AppBuilder SD2.1 backend is unavailable")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(60)
        host, port = listener.getsockname()
        token = secrets.token_hex(24)
        if getattr(sys, "frozen", False):
            command = [
                str(_worker_python()),
                "--qai-appbuilder-sd21-worker",
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
            worker_cwd = Path(__file__).resolve().parents[1]
        process = subprocess.Popen(
            command,
            cwd=str(worker_cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        try:
            channel, _ = listener.accept()
            channel.settimeout(300)
            reader = channel.makefile("r", encoding="utf-8")
            writer = channel.makefile("w", encoding="utf-8")
            response = json.loads(reader.readline())
            if (
                not response.get("ok")
                or response.get("event") != "ready"
                or response.get("token") != token
            ):
                raise RuntimeError(response.get("error", "QAI SD2.1 worker failed to start"))
        except Exception:
            process.terminate()
            process.wait(timeout=10)
            raise
        finally:
            listener.close()
        self._process = process
        self._channel = channel
        self._reader = reader
        self._writer = writer
        return process

    def generate(self, job):
        response = super().generate(job)
        if response.success:
            response.message = "QAI AppBuilder SD2.1 generation completed"
            response.backend_name = BACKEND_NAME
            response.metadata["backend"] = BACKEND_NAME
        return response


def _send_ready_error(writer, token: str, error: Exception) -> int:
    writer.write(
        json.dumps({"ok": False, "event": "ready", "token": token, "error": str(error)})
        + "\n"
    )
    writer.flush()
    return 1


def _worker_main() -> int:
    worker_flag = "--qai-appbuilder-sd21-worker" if getattr(sys, "frozen", False) else "--worker"
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
        from qai_appbuilder import PerfProfile, QNNShareMemory
    except Exception as exc:
        return _send_ready_error(writer, token, exc)

    common_dir = (
        Path(sys.executable).resolve().parent / "qai_appbuilder_common"
        if getattr(sys, "frozen", False)
        else _qai_root() / "samples" / "common"
    )
    sys.path.insert(0, str(common_dir))
    try:
        from _stable_diffusion import (
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
        return _send_ready_error(writer, token, exc)

    class TextEncoder(TextEncoderBase):
        _embed_dim = 1024

    class Unet(UnetBase):
        pass

    class VaeDecoder(VaeDecoderBase):
        pass

    model_dir = _model_dir()
    tokenizer = text_encoder = unet = vae_decoder = scheduler = share_memory = None
    try:
        set_qnn_config()
        tokenizer = load_tokenizer(
            "stabilityai/stable-diffusion-2-1-base",
            model_dir / "tokenizer",
            "Local Qualcomm SD2.1 tokenizer is required",
            use_subfolder=True,
        )
        text_encoder = TextEncoder("text_encoder", str(model_dir / _MODEL_FILES[0]))
        unet = Unet("model_unet", str(model_dir / _MODEL_FILES[1]))
        vae_decoder = VaeDecoder("vae_decoder", str(model_dir / _MODEL_FILES[2]))
        share_memory = QNNShareMemory("share_memory", 50 * 1024 * 1024)
        scheduler = make_scheduler()
        PerfProfile.SetPerfProfileGlobal(PerfProfile.BURST)
        writer.write(
            json.dumps({"ok": True, "event": "ready", "worker_pid": os.getpid(), "token": token})
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
                    raise ValueError("QAI SD2.1 supports only 512x512")
                steps = int(job.get("steps", 20))
                guidance = float(job.get("cfg_scale", 7.5))
                seed = int(job.get("seed", -1))
                if seed < 0:
                    seed = int(np.random.randint(0, 9_999_999_999, dtype=np.int64))
                scheduler.set_timesteps(steps)
                start = time.perf_counter()
                cond_tokens = run_tokenizer(tokenizer, str(job.get("prompt", "")), 77)
                uncond_tokens = run_tokenizer(tokenizer, str(job.get("negative_prompt", "")), 77)
                uncond_embedding = text_encoder.Inference(uncond_tokens).copy()
                cond_embedding = text_encoder.Inference(cond_tokens).copy()
                latent = generate_initial_latent(seed=np.int64(seed))
                for index in range(steps):
                    timestep = get_timestep(scheduler, index)
                    noise_uncond = unet.Inference(latent, timestep, uncond_embedding).copy()
                    noise_cond = unet.Inference(latent, timestep, cond_embedding).copy()
                    latent = run_scheduler(
                        scheduler, noise_uncond, noise_cond, latent, timestep, guidance
                    )
                output_raw = vae_decoder.Inference(latent)
                generation_time = time.perf_counter() - start
                if len(output_raw) == 0:
                    raise RuntimeError("VAE returned no image data")
                image: Image.Image = decode_vae_output(output_raw)
                output_dir = Path(str(job.get("output_directory", "output"))).resolve()
                output_dir.mkdir(parents=True, exist_ok=True)
                image_path = output_dir / f"{job.get('output_prefix', 'generate')}_{str(job.get('job_id', ''))[:8]}.png"
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
            except Exception as exc:
                writer.write(json.dumps({"ok": False, "error": str(exc)}) + "\n")
                writer.flush()
    except Exception as exc:
        return _send_ready_error(writer, token, exc)
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
        del share_memory, scheduler, vae_decoder, unet, text_encoder, tokenizer
        gc.collect()
        reader.close()
        writer.close()
        channel.close()
    return 0


_SHARED_BACKEND: StableDiffusion21QaiAppBuilderBackend | None = None
_SHARED_BACKEND_LOCK = threading.Lock()


def get_shared_backend() -> StableDiffusion21QaiAppBuilderBackend:
    global _SHARED_BACKEND
    with _SHARED_BACKEND_LOCK:
        if _SHARED_BACKEND is None:
            _SHARED_BACKEND = StableDiffusion21QaiAppBuilderBackend()
            atexit.register(_SHARED_BACKEND.close)
        return _SHARED_BACKEND


if __name__ == "__main__" and "--worker" in sys.argv:
    raise SystemExit(_worker_main())
