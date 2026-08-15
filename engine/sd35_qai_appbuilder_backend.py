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
    _worker_python,
)


BACKEND_NAME = "Qualcomm SD3.5 Medium QAI AppBuilder (HTP)"
MODEL_ID = "stable_diffusion_v3_5_qai"
_MODEL_FILES = (
    "serialized_binaries/text_encoder.serialized.bin",
    "serialized_binaries/text_encoder_2.serialized.bin",
    "serialized_binaries/transformer.serialized.bin",
    "serialized_binaries/vae_decoder.serialized.bin",
    "time_text_embed.pt",
)


def _model_dir() -> Path:
    configured = os.environ.get("SNAPDRAGON_QAI_SD35_MODEL_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    canonical = MODELS_DIR / MODEL_ID
    if canonical.is_dir() or not getattr(sys, "frozen", False):
        return canonical
    legacy = Path(sys.executable).resolve().parent / "models" / MODEL_ID
    return legacy if legacy.is_dir() else canonical


def _has_tokenizer(model_dir: Path, name: str) -> bool:
    tokenizer_dir = model_dir / name
    return (
        tokenizer_dir.is_dir()
        and (tokenizer_dir / "tokenizer_config.json").is_file()
        and (tokenizer_dir / "vocab.json").is_file()
        and (tokenizer_dir / "merges.txt").is_file()
    )


class StableDiffusion35QaiAppBuilderBackend(StableDiffusion15QaiAppBuilderBackend):
    """Persistent, process-isolated Qualcomm SD3.5 Medium backend."""

    def get_backend_name(self) -> str:
        return BACKEND_NAME

    def get_supported_models(self) -> list[str]:
        return [MODEL_ID]

    def is_available(self) -> bool:
        python = _worker_python()
        model_dir = _model_dir()
        if (
            not python.is_file()
            or not all((model_dir / name).is_file() for name in _MODEL_FILES)
            or not _has_tokenizer(model_dir, "tokenizer")
            or not _has_tokenizer(model_dir, "tokenizer_2")
        ):
            return False
        probe = (
            "from qai_appbuilder import QNNConfig,QNNContext,Runtime,LogLevel,ProfilingLevel; "
            "import torch,transformers,diffusers; "
            "QNNConfig.Config(Runtime.HTP,LogLevel.ERROR,ProfilingLevel.BASIC)"
        )
        try:
            command = (
                [str(python), "--qai-appbuilder-probe"]
                if getattr(sys, "frozen", False)
                else [str(python), "-c", probe]
            )
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=20, check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return completed.returncode == 0

    def _ensure_worker(self) -> subprocess.Popen[str]:
        process = self._process
        if process is not None and process.poll() is None:
            return process
        if not self.is_available():
            raise RuntimeError("QAI AppBuilder SD3.5 Medium backend is unavailable")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(120)
        host, port = listener.getsockname()
        token = secrets.token_hex(24)
        if getattr(sys, "frozen", False):
            command = [str(_worker_python()), "--qai-appbuilder-sd35-worker", host, str(port), token]
            worker_cwd = Path(sys.executable).resolve().parent
        else:
            command = [str(_worker_python()), str(Path(__file__).resolve()), "--worker", host, str(port), token]
            worker_cwd = _PROJECT_ROOT
        process = subprocess.Popen(
            command,
            cwd=str(worker_cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            channel, _ = listener.accept()
            channel.settimeout(600)
            reader = channel.makefile("r", encoding="utf-8")
            writer = channel.makefile("w", encoding="utf-8")
            response = json.loads(reader.readline())
            if not response.get("ok") or response.get("event") != "ready" or response.get("token") != token:
                raise RuntimeError(response.get("error", "QAI SD3.5 worker failed to start"))
        except Exception:
            process.terminate()
            process.wait(timeout=15)
            raise
        finally:
            listener.close()
        self._process = process
        self._channel = channel
        self._reader = reader
        self._writer = writer
        return process

    def _read_response(self, process: subprocess.Popen[str]) -> dict[str, Any]:
        if self._reader is None:
            raise RuntimeError("QAI worker channel is unavailable")
        while True:
            line = self._reader.readline()
            if not line:
                raise RuntimeError("QAI worker exited without a response")
            try:
                data = json.loads(line)
                if isinstance(data, dict) and data.get("event") == "progress":
                    percent = data.get("percent", 0)
                    stage = data.get("stage", "")
                    job = getattr(self, "_current_job", None)
                    if job is not None:
                        job.report_progress(percent / 100.0, stage)
                    continue
                return data
            except json.JSONDecodeError:
                continue

    def generate(self, job):
        self._current_job = job
        try:
            response = super().generate(job)
        finally:
            self._current_job = None
        if response.success:
            response.backend_name = BACKEND_NAME
            response.metadata["backend"] = BACKEND_NAME
        return response


def _send_ready_error(writer, token: str, error: Exception) -> int:
    writer.write(json.dumps({"ok": False, "event": "ready", "token": token, "error": str(error)}) + "\n")
    writer.flush()
    return 1


def _worker_main() -> int:
    worker_flag = "--qai-appbuilder-sd35-worker" if getattr(sys, "frozen", False) else "--worker"
    flag_index = sys.argv.index(worker_flag)
    host, port, token = sys.argv[flag_index + 1], int(sys.argv[flag_index + 2]), sys.argv[flag_index + 3]
    channel = socket.create_connection((host, port), timeout=30)
    reader = channel.makefile("r", encoding="utf-8")
    writer = channel.makefile("w", encoding="utf-8")

    try:
        import numpy as np
        import torch
        from PIL import Image
        from diffusers import FlowMatchEulerDiscreteScheduler
        from diffusers.models.embeddings import CombinedTimestepTextProjEmbeddings
        from qai_appbuilder import LogLevel, PerfProfile, ProfilingLevel, QNNConfig, QNNContext, Runtime
        from transformers import CLIPTokenizer
    except Exception as exc:
        return _send_ready_error(writer, token, exc)

    class TextEncoderCLIPL(QNNContext):
        def Inference(self, token_ids):
            outputs = super().Inference([np.ascontiguousarray(token_ids, dtype=np.float32).reshape(-1)])
            return (outputs[1], outputs[0]) if outputs[0].size == 768 else (outputs[0], outputs[1])

    class TextEncoderCLIPG(QNNContext):
        def Inference(self, token_ids):
            outputs = super().Inference([np.ascontiguousarray(token_ids, dtype=np.float32).reshape(-1)])
            return (outputs[1], outputs[0]) if outputs[0].size == 1280 else (outputs[0], outputs[1])

    class TransformerQNN(QNNContext):
        def Inference(self, temb, hidden_states, encoder_hidden_states):
            arrays = [
                np.ascontiguousarray(temb, dtype=np.float32).reshape(-1),
                np.ascontiguousarray(hidden_states, dtype=np.float32).reshape(-1),
                np.ascontiguousarray(encoder_hidden_states, dtype=np.float32).reshape(-1),
            ]
            by_size = {array.size: array for array in arrays}
            ordered = [by_size[int(np.prod(shape))] for shape in self.getInputShapes()]
            return super().Inference(ordered)[0].reshape(1, 4096, 64)

    class VaeDecoder(QNNContext):
        def Inference(self, sample):
            return super().Inference([np.ascontiguousarray(sample, dtype=np.float32).reshape(-1)])[0]

    def tokenize(prompt, tokenizer):
        ids = tokenizer(prompt, padding="max_length", max_length=77, truncation=True).input_ids
        return np.asarray(ids, dtype=np.float32).reshape(1, 77)

    def encoder_hidden_states(hidden1, hidden2):
        combined = np.concatenate((hidden1.reshape(1, 77, -1), hidden2.reshape(1, 77, -1)), axis=-1)
        combined = np.pad(combined, ((0, 0), (0, 0), (0, 2048)))
        return np.concatenate((combined, np.zeros((1, 83, 4096), dtype=np.float32)), axis=1).astype(np.float32)

    def pooled_projection(pooled1, pooled2):
        return np.concatenate((pooled1.reshape(1, -1), pooled2.reshape(1, -1)), axis=-1).astype(np.float32)

    def unpatchify(noise):
        result = noise.reshape(1, 64, 64, 2, 2, 16).transpose(0, 5, 1, 3, 2, 4)
        return result.reshape(1, 16, 128, 128).astype(np.float32)

    model_dir = _model_dir()
    tokenizer = tokenizer_2 = time_text_embed = scheduler = None
    text_encoder = text_encoder_2 = transformer = vae_decoder = None
    try:
        QNNConfig.Config(Runtime.HTP, LogLevel.WARN, ProfilingLevel.BASIC, "")
        os.environ["TOKENIZERS_PARALLELISM"] = "0"
        tokenizer = CLIPTokenizer.from_pretrained(model_dir / "tokenizer", local_files_only=True)
        tokenizer_2 = CLIPTokenizer.from_pretrained(model_dir / "tokenizer_2", local_files_only=True)
        checkpoint = torch.load(model_dir / "time_text_embed.pt", map_location="cpu", weights_only=True)
        state_dict = checkpoint["state_dict"]
        time_text_embed = CombinedTimestepTextProjEmbeddings(
            embedding_dim=state_dict["timestep_embedder.linear_1.weight"].shape[0],
            pooled_projection_dim=state_dict["text_embedder.linear_1.weight"].shape[1],
        )
        time_text_embed.load_state_dict(state_dict)
        time_text_embed.eval()
        scheduler = FlowMatchEulerDiscreteScheduler(num_train_timesteps=1000, shift=3.0)
        bins = model_dir / "serialized_binaries"
        text_encoder = TextEncoderCLIPL("text_encoder", str(bins / "text_encoder.serialized.bin"))
        text_encoder_2 = TextEncoderCLIPG("text_encoder_2", str(bins / "text_encoder_2.serialized.bin"))
        vae_decoder = VaeDecoder("vae_decoder", str(bins / "vae_decoder.serialized.bin"))
        transformer = TransformerQNN("transformer", str(bins / "transformer.serialized.bin"))
        PerfProfile.SetPerfProfileGlobal(PerfProfile.BURST)
        writer.write(json.dumps({"ok": True, "event": "ready", "worker_pid": os.getpid(), "token": token}) + "\n")
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
                if int(job.get("width", 1024)) != 1024 or int(job.get("height", 1024)) != 1024:
                    raise ValueError("QAI SD3.5 Medium supports only 1024x1024")
                steps = int(job.get("steps", 8))
                guidance = float(job.get("cfg_scale", 3.5))
                seed = int(job.get("seed", -1))
                if seed < 0:
                    seed = int(np.random.randint(0, 4294967296, dtype=np.int64))
                elif seed > 4294967295:
                    seed = int(seed % 4294967296)
                start = time.perf_counter()
                prompt, negative = str(job.get("prompt", "")), str(job.get("negative_prompt", ""))
                
                writer.write(json.dumps({"event": "progress", "percent": 10, "stage": "Modell wird geladen (Text Encoder)..."}) + "\n")
                writer.flush()

                h1c, p1c = text_encoder.Inference(tokenize(prompt, tokenizer))
                h2c, p2c = text_encoder_2.Inference(tokenize(prompt, tokenizer_2))
                h1u, p1u = text_encoder.Inference(tokenize(negative, tokenizer))
                h2u, p2u = text_encoder_2.Inference(tokenize(negative, tokenizer_2))
                cond_hs, uncond_hs = encoder_hidden_states(h1c, h2c), encoder_hidden_states(h1u, h2u)
                cond_pool, uncond_pool = pooled_projection(p1c, p2c), pooled_projection(p1u, p2u)
                
                writer.write(json.dumps({"event": "progress", "percent": 25, "stage": "Modell wird geladen..."}) + "\n")
                writer.flush()

                latent = np.random.RandomState(seed).randn(1, 16, 128, 128).astype(np.float32)
                scheduler.set_timesteps(steps)
                total_steps = len(scheduler.timesteps)
                for index, timestep in enumerate(scheduler.timesteps):
                    # Report progress
                    sampling_progress = index / total_steps
                    progress = 0.30 + (sampling_progress * 0.55)
                    percent = int(progress * 100)
                    step_num = index + 1
                    writer.write(json.dumps({
                        "event": "progress",
                        "percent": percent,
                        "stage": f"Sampling Phase (Schritt {step_num}/{total_steps})...."
                    }) + "\n")
                    writer.flush()

                    t_value = timestep.item()
                    t_tensor = torch.tensor([t_value], dtype=torch.float32)
                    with torch.no_grad():
                        cond_temb = time_text_embed(t_tensor, torch.from_numpy(cond_pool)).numpy().astype(np.float32)
                        uncond_temb = time_text_embed(t_tensor, torch.from_numpy(uncond_pool)).numpy().astype(np.float32)
                    latent_nhwc = latent.transpose(0, 2, 3, 1).astype(np.float32)
                    noise_cond = unpatchify(transformer.Inference(cond_temb, latent_nhwc, cond_hs))
                    noise_uncond = unpatchify(transformer.Inference(uncond_temb, latent_nhwc, uncond_hs))
                    noise = noise_uncond + guidance * (noise_cond - noise_uncond)
                    latent = scheduler.step(torch.from_numpy(noise), timestep, torch.from_numpy(latent)).prev_sample.numpy().astype(np.float32)
                
                writer.write(json.dumps({"event": "progress", "percent": 90, "stage": "VAE Decoding..."}) + "\n")
                writer.flush()

                sample = (latent / 1.5305 + 0.0609).astype(np.float32).transpose(0, 2, 3, 1)
                output = vae_decoder.Inference(sample)
                image_array = output.reshape(1, 1024, 1024, 3) / 2.0 + 0.5
                image = Image.fromarray(np.clip(image_array[0] * 255.0, 0, 255).astype(np.uint8), mode="RGB")
                
                writer.write(json.dumps({"event": "progress", "percent": 95, "stage": "Bild wird gespeichert & Metadaten geschrieben..."}) + "\n")
                writer.flush()

                output_dir = Path(str(job.get("output_directory", "output"))).resolve()
                output_dir.mkdir(parents=True, exist_ok=True)
                image_path = output_dir / f"{job.get('output_prefix', 'generate')}_{str(job.get('job_id', ''))[:8]}.png"
                image.save(image_path, format="PNG")
                writer.write(json.dumps({"ok": True, "image_path": str(image_path), "generation_time": time.perf_counter() - start, "worker_pid": os.getpid(), "seed": seed}) + "\n")
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
        for context in (vae_decoder, transformer, text_encoder_2, text_encoder):
            if context is not None:
                try:
                    context.release()
                except Exception:
                    pass
        del vae_decoder, transformer, text_encoder_2, text_encoder, scheduler, time_text_embed
        gc.collect()
        reader.close()
        writer.close()
        channel.close()
    return 0


_SHARED_BACKEND: StableDiffusion35QaiAppBuilderBackend | None = None
_SHARED_BACKEND_LOCK = threading.Lock()


def get_shared_backend() -> StableDiffusion35QaiAppBuilderBackend:
    global _SHARED_BACKEND
    with _SHARED_BACKEND_LOCK:
        if _SHARED_BACKEND is None:
            _SHARED_BACKEND = StableDiffusion35QaiAppBuilderBackend()
            atexit.register(_SHARED_BACKEND.close)
        return _SHARED_BACKEND


if __name__ == "__main__" and "--worker" in sys.argv:
    raise SystemExit(_worker_main())
