#!/usr/bin/env python3
"""
Qualcomm ControlNet Canny QNN Backend.
Subclasses InferenceBackend to run ControlNet Canny precompiled context models on Qualcomm Hexagon HTP.
Utilizes a subprocess worker to isolate QAIRT 2.45.41 from QAIRT 2.47 system drivers.
"""

from __future__ import annotations

import html
import json
import logging
import os
import platform
import sys
import shutil
from pathlib import Path
import time
from typing import Any
import numpy as np

# Ensure global site-packages is appended to import PIL if needed
global_site_packages = r"C:\Program Files\Python311-arm64\Lib\site-packages"
if global_site_packages not in sys.path:
    sys.path.append(global_site_packages)

# Add project root to sys.path to resolve controllers and engine packages in subprocess
project_root = str(Path(__file__).parent.parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.i18n import tr
from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse
from engine.inference_backend import InferenceBackend
from engine.logging_config import get_logger

logger = get_logger("ControlNetCannyQnnBackend")
DEFAULT_NEGATIVE_PROMPT = "blurry, low quality, distorted"


def _resolve_negative_prompt(job_data: dict[str, Any]) -> str:
    """Use the fallback only when the field is absent; preserve an explicit empty value."""
    return str(job_data["negative_prompt"]) if "negative_prompt" in job_data else DEFAULT_NEGATIVE_PROMPT


def _read_git_commit() -> str:
    try:
        git_dir = Path(__file__).parent.parent / ".git"
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            return (git_dir / head[5:]).read_text(encoding="utf-8").strip()[:7]
        return head[:7]
    except OSError:
        return "unknown"


def _tensor_summary(name: str, value: np.ndarray) -> dict[str, Any]:
    """Return compact tensor diagnostics without serializing tensor values."""
    array = np.asarray(value)
    return {
        "name": name,
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "min": float(array.min()),
        "max": float(array.max()),
        "mean": float(array.mean()),
        "standard_deviation": float(array.std()),
    }


def bytes_to_unicode() -> dict[int, str]:
    bs = list(range(ord("!"), ord("~")+1))+list(range(ord("¡"), ord("¬")+1))+list(range(ord("®"), ord("ÿ")+1))
    cs = bs[:]
    n = 0
    for b in range(2**8):
        if b not in bs:
            bs.append(b)
            cs.append(2**8+n)
            n += 1
    cs = [chr(n) for n in cs]
    return dict(zip(bs, cs))


class SimpleCLIPTokenizer:
    def __init__(self, vocab_path: str | Path, merges_path: str | Path) -> None:
        import re
        with open(vocab_path, 'r', encoding='utf-8') as f:
            self.encoder = json.load(f)
        self.decoder = {v: k for k, v in self.encoder.items()}
        self.byte_encoder = bytes_to_unicode()
        self.pat = re.compile(
            r"""<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|[^\W\d_]+|\d+|(?:[^\s\w]|_)+""",
            re.IGNORECASE,
        )
        
        with open(merges_path, 'r', encoding='utf-8') as f:
            merges = f.read().split('\n')
        bpe_merges = []
        for line in merges:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            bpe_merges.append(tuple(line.split()))
        self.bpe_ranks = dict(zip(bpe_merges, range(len(bpe_merges))))
        self.cache = {}

    def bpe(self, token: str) -> str:
        if token in self.cache:
            return self.cache[token]
        word = tuple(token[:-1]) + (token[-1] + '</w>',)
        pairs = self.get_pairs(word)
        if not pairs:
            return token + '</w>'
        while True:
            bigram = min(pairs, key=lambda pair: self.bpe_ranks.get(pair, float('inf')))
            if bigram not in self.bpe_ranks:
                break
            first, second = bigram
            new_word = []
            i = 0
            while i < len(word):
                try:
                    j = word.index(first, i)
                    new_word.extend(word[i:j])
                    i = j
                except ValueError:
                    new_word.extend(word[i:])
                    break
                if word[i] == first and i < len(word)-1 and word[i+1] == second:
                    new_word.append(first+second)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            word = tuple(new_word)
            if len(word) == 1:
                break
            else:
                pairs = self.get_pairs(word)
        word = ' '.join(word)
        self.cache[token] = word
        return word

    def get_pairs(self, word: tuple[str, ...]) -> set[tuple[str, str]]:
        pairs = set()
        prev_char = word[0]
        for char in word[1:]:
            pairs.add((prev_char, char))
            prev_char = char
        return pairs

    def encode(self, text: str) -> list[int]:
        import re
        bpe_tokens = []
        text = html.unescape(html.unescape(text))
        text = re.sub(r'\s+', ' ', text.lower()).strip()
        for token in re.findall(self.pat, text):
            token = "".join(self.byte_encoder[b] for b in token.encode('utf-8'))
            bpe_tokens.extend(self.bpe(token).split(' '))
        return [self.encoder[bpe_token] for bpe_token in bpe_tokens]

    def tokenize_prompt(self, prompt: str, max_length: int = 77) -> list[int]:
        eos_token_id = 49407
        ids = [49406] + self.encode(prompt) + [49407]
        if len(ids) < max_length:
            ids = ids + [eos_token_id] * (max_length - len(ids))
        else:
            ids = ids[:max_length]
            ids[-1] = eos_token_id
        return ids


# 1. Custom pure-NumPy Canny Edge Detector (CPU)
def gaussian_kernel(size, sigma=1.0):
    size = int(size) // 2
    x, y = np.mgrid[-size:size+1, -size:size+1]
    normal = 1 / (2.0 * np.pi * sigma**2)
    g = np.exp(-((x**2 + y**2) / (2.0 * sigma**2))) * normal
    return g

def convolve2d(image, kernel):
    kernel = np.flipud(np.fliplr(kernel))
    sub_shape = kernel.shape
    view_shape = tuple(np.subtract(image.shape, sub_shape) + 1) + sub_shape
    strides = image.strides + image.strides
    sub_matrices = np.lib.stride_tricks.as_strided(image, view_shape, strides)
    return np.einsum('ij,klij->kl', kernel, sub_matrices)

def preprocess_image_aspect_ratio(img, target_size=(512, 512)):
    """
    Resize and crop an image to target_size (512x512) while preserving the original aspect ratio
    using smart center cropping.
    """
    from PIL import Image
    w, h = img.size
    target_w, target_h = target_size

    aspect = w / h
    target_aspect = target_w / target_h

    if aspect > target_aspect:
        # Image is wider than target aspect ratio: Crop left and right sides
        new_w = int(h * target_aspect)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif aspect < target_aspect:
        # Image is taller than target aspect ratio: Crop top and bottom sides
        new_h = int(w / target_aspect)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    return img.resize(target_size, Image.Resampling.LANCZOS)

def canny_edge_detector(img_path, low_threshold=50, high_threshold=150):
    from PIL import Image
    img = Image.open(img_path).convert('L')
    img = preprocess_image_aspect_ratio(img, (512, 512))
    img_arr = np.array(img, dtype=np.float32)
    
    # Blur
    kernel = gaussian_kernel(5, sigma=1.4)
    padded_img = np.pad(img_arr, 2, mode='edge')
    blurred = convolve2d(padded_img, kernel)
    
    # Gradients (Sobel)
    Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    Ky = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]], dtype=np.float32)
    
    padded_blurred = np.pad(blurred, 1, mode='edge')
    Ix = convolve2d(padded_blurred, Kx)
    Iy = convolve2d(padded_blurred, Ky)
    
    G = np.hypot(Ix, Iy)
    if G.max() > 0:
        G = G / G.max() * 255.0
    theta = np.arctan2(Iy, Ix)
    
    # Non-Maximum Suppression
    M, N = G.shape
    Z = np.zeros((M, N), dtype=np.int32)
    angle = theta * 180. / np.pi
    angle[angle < 0] += 180.0
    
    for i in range(1, M-1):
        for j in range(1, N-1):
            q = 255
            r = 255
            if (0 <= angle[i,j] < 22.5) or (157.5 <= angle[i,j] <= 180):
                q = G[i, j+1]
                r = G[i, j-1]
            elif (22.5 <= angle[i,j] < 67.5):
                q = G[i+1, j-1]
                r = G[i-1, j+1]
            elif (67.5 <= angle[i,j] < 112.5):
                q = G[i+1, j]
                r = G[i-1, j]
            elif (112.5 <= angle[i,j] < 157.5):
                q = G[i-1, j-1]
                r = G[i+1, j+1]

            if (G[i,j] >= q) and (G[i,j] >= r):
                Z[i,j] = G[i,j]
            else:
                Z[i,j] = 0
                
    # Double threshold
    res = np.zeros((M,N), dtype=np.int32)
    weak = np.int32(25)
    strong = np.int32(255)
    
    strong_i, strong_j = np.where(Z >= high_threshold)
    weak_i, weak_j = np.where((Z >= low_threshold) & (Z < high_threshold))
    
    res[strong_i, strong_j] = strong
    res[weak_i, weak_j] = weak
    
    # Hysteresis
    for i in range(1, M-1):
        for j in range(1, N-1):
            if (res[i,j] == weak):
                if ((res[i+1, j-1] == strong) or (res[i+1, j] == strong) or (res[i+1, j+1] == strong)
                    or (res[i, j-1] == strong) or (res[i, j+1] == strong)
                    or (res[i-1, j-1] == strong) or (res[i-1, j] == strong) or (res[i-1, j+1] == strong)):
                    res[i, j] = strong
                else:
                    res[i, j] = 0
    return res.astype(np.uint8)


# 2. Custom pure-NumPy DDIM Scheduler (CPU)
class DDIMScheduler:
    def __init__(self, num_train_timesteps: int = 1000, beta_start: float = 0.00085, beta_end: float = 0.012) -> None:
        self.num_train_timesteps = num_train_timesteps
        self.betas = np.linspace(beta_start**0.5, beta_end**0.5, num_train_timesteps, dtype=np.float32)**2
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = np.cumprod(self.alphas, axis=0)

    def set_timesteps(self, num_inference_steps: int) -> None:
        step_ratio = self.num_train_timesteps // num_inference_steps
        self.timesteps = (np.arange(num_inference_steps) * step_ratio).round()[::-1].astype(np.int32) + 1
        self.final_alpha_cumprod = self.alphas_cumprod[0]

    def step(self, model_output: np.ndarray, timestep: int, sample: np.ndarray, step_ratio: int) -> np.ndarray:
        previous_timestep = timestep - step_ratio
        alpha_t = self.alphas_cumprod[timestep]
        alpha_previous = self.alphas_cumprod[previous_timestep] if previous_timestep >= 0 else self.final_alpha_cumprod
        
        pred_original_sample = (sample - (1.0 - alpha_t)**0.5 * model_output) / alpha_t**0.5
        pred_dir_latent = (1.0 - alpha_previous)**0.5 * model_output
        prev_sample = alpha_previous**0.5 * pred_original_sample + pred_dir_latent
        return prev_sample


class ControlNetCannyQnnBackend(InferenceBackend):
    """
    Physical backend executing ControlNet Canny on Snapdragon HTP NPU via QNN EP.
    """

    @staticmethod
    def requantize_tensor_static(arr_q, scale_from, zp_from, scale_to, zp_to, factor=1.0):
        arr_f = (arr_q.astype(np.float32) - zp_from) * scale_from
        if factor != 1.0:
            arr_f = arr_f * factor
        arr_q_to = np.round(arr_f / scale_to) + zp_to
        clipped_low = np.sum(arr_q_to < 0)
        clipped_high = np.sum(arr_q_to > 65535)
        clipped_arr = np.clip(arr_q_to, 0, 65535).astype(np.uint16)
        return clipped_arr, int(clipped_low), int(clipped_high)

    def __init__(self) -> None:
        self._active_process = None


    def cancel(self, job: GenerationJob) -> str:
        """Terminate the worker subprocess that owns the active QNN sessions."""
        import subprocess

        from engine.job_lifecycle import cancel_job

        cancel_job(job)
        process = self._active_process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        return "CANCELLED"

    def shutdown(self) -> None:
        """Release worker handles and host-side references without changing job state."""
        import subprocess

        process = self._active_process
        try:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            stdout = getattr(process, "stdout", None)
            if stdout is not None:
                stdout.close()
        finally:
            self._active_process = None

    def _setup_sessions(self, model_dir: Path, temp_dir: Path) -> tuple[Any, Any, Any, Any, dict[str, Any]]:
        import onnxruntime as ort
        import onnxruntime_qnn as qnn

        # Introspect ORT and devices
        has_devices_api = hasattr(ort, "get_ep_devices") and hasattr(ort.SessionOptions, "add_provider_for_devices")
        if not has_devices_api:
            raise RuntimeError("ORT does not support required get_ep_devices or add_provider_for_devices APIs")

        print("Preparing Qualcomm QNN runtime for ControlNet Canny", flush=True)
        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())

        all_devices = ort.get_ep_devices()
        selected_devices = [d for d in all_devices if d.ep_name == "QNNExecutionProvider"]
        if not selected_devices:
            raise RuntimeError("No QNNExecutionProvider devices found in get_ep_devices()")

        # Create session configurations
        options = ort.SessionOptions()
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        options.enable_profiling = True
        options.profile_file_prefix = str(temp_dir / "ort_profile")

        provider_options = {"backend_path": qnn.get_qnn_htp_path()}
        options.add_provider_for_devices(selected_devices, provider_options)

        print("Loading Text Encoder on HTP", flush=True)
        text_encoder_session = ort.InferenceSession(str(model_dir / "text_encoder.onnx"), sess_options=options)

        print("Loading ControlNet on HTP", flush=True)
        controlnet_session = ort.InferenceSession(str(model_dir / "controlnet.onnx"), sess_options=options)

        print("Loading UNet on HTP", flush=True)
        unet_session = ort.InferenceSession(str(model_dir / "unet.onnx"), sess_options=options)

        print("Loading VAE on HTP", flush=True)
        vae_session = ort.InferenceSession(str(model_dir / "vae.onnx"), sess_options=options)

        provider_diagnostics = {
            "qnn_version": qnn.__version__,
            "ort_version": ort.__version__,
            "backend_path": qnn.get_qnn_htp_path(),
            "provider_library": qnn.get_library_path()
        }

        return text_encoder_session, controlnet_session, unet_session, vae_session, provider_diagnostics

    def generate(self, job: GenerationJob) -> GenerationResponse:
        params = job.parameters
        logger.info("[Main Process] Spawning worker subprocess for ControlNet Canny QNN...")
        print("[Main Process] Spawning worker subprocess for ControlNet Canny QNN...")

        if job.cancel_requested.is_set():
            return GenerationResponse(
                success=False,
                status="CANCELLED",
                message=tr("generation_cancelled", "Generierung abgebrochen."),
                model_name=params.model_name,
            )

        temp_dir = Path(r"C:\SnapdragonAI\temp\controlnet_canny_gate")
        temp_dir.mkdir(parents=True, exist_ok=True)
        job_id_str = str(job.job_id)[:8]
        input_json_path = temp_dir / f"job_input_{job_id_str}.json"
        output_json_path = temp_dir / f"job_output_{job_id_str}.json"
        output_json_path.unlink(missing_ok=True)

        # Serialize job parameters
        job_data = job.parameters.to_worker_dict(job.job_id)


        with open(input_json_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, indent=2)

        # Run subprocess using the venv python executable
        venv_python = r"C:\SnapdragonAI\temp\controlnet_canny_gate\venv\Scripts\python.exe"
        script_path = Path(__file__).resolve()

        import subprocess
        cmd = [
            venv_python,
            str(script_path),
            str(input_json_path),
            str(output_json_path)
        ]

        logger.info(f"Executing: {' '.join(cmd)}")
        worker_output: list[str] = []
        worker_env = os.environ.copy()
        worker_env["PYTHONPATH"] = os.pathsep.join(
            part for part in (project_root, worker_env.get("PYTHONPATH", "")) if part
        )

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=project_root,
            env=worker_env,
        )
        self._active_process = process

        # Read output in real-time to update status/progress
        while True:
            line = process.stdout.readline()
            if job.cancel_requested.is_set():
                self.cancel(job)
                input_json_path.unlink(missing_ok=True)
                output_json_path.unlink(missing_ok=True)
                self._active_process = None
                return GenerationResponse(
                    success=False,
                    status="CANCELLED",
                    message=tr("generation_cancelled", "Generierung abgebrochen."),
                    model_name=params.model_name,
                )
            if not line and process.poll() is not None:
                break
            if line:
                line_str = line.strip()
                worker_output.append(line_str)
                logger.info("[QNN Worker] %s", line_str)
                if not job.cancel_requested.is_set() and any(k in line_str for k in ["Preparing", "Loading", "Starting", "Tokenizing", "Running", "Decoding", "Saving", "Step", "Image", "Computing"]):
                    from engine.generation_progress import report_qnn_progress
                    report_qnn_progress(job, line_str)

        process.wait()
        self._active_process = None

        if job.cancel_requested.is_set():
            input_json_path.unlink(missing_ok=True)
            output_json_path.unlink(missing_ok=True)
            return GenerationResponse(
                success=False,
                status="CANCELLED",
                message=tr("generation_cancelled", "Generierung abgebrochen."),
                model_name=params.model_name,
            )

        # Check if output json exists
        if not output_json_path.exists():
            logger.error(
                "QNN worker produced no output JSON | exit_code=%s | command=%s | cwd=%s | output=%s",
                process.returncode,
                cmd,
                project_root,
                "\n".join(worker_output) or "<empty>",
            )
            return GenerationResponse(
                success=False,
                status="PipelineError",
                message=tr(
                    "generation_worker_failed",
                    "Die Generierung konnte nicht abgeschlossen werden. Details wurden protokolliert.",
                ),
                model_name=params.model_name
            )

        try:
            with open(output_json_path, "r", encoding="utf-8") as f:
                result_data = json.load(f)
        except (OSError, json.JSONDecodeError):
            logger.exception(
                "QNN worker output JSON is unreadable | exit_code=%s | path=%s | output=%s",
                process.returncode,
                output_json_path,
                "\n".join(worker_output) or "<empty>",
            )
            result_data = {"success": False}

        # Clean up temp files
        try:
            input_json_path.unlink(missing_ok=True)
            output_json_path.unlink(missing_ok=True)
        except Exception:
            pass

        image_path = result_data.get("image_path")
        if result_data.get("success") and image_path and Path(image_path).is_file():
            return GenerationResponse(
                success=True,
                status="FINISHED",
                message=result_data.get("message", tr("generation_completed", "Generierung abgeschlossen.")),
                image_path=image_path,
                thumbnail_path=image_path,
                generation_time=result_data.get("generation_time", 0.0),
                backend_name="Qualcomm ControlNet Canny (HTP V73)",
                model_name=params.model_name,
                metadata=result_data.get("metadata", {})
            )
        else:
            logger.error(
                "QNN worker generation failed | exit_code=%s | detail=%s | image_path=%s",
                process.returncode,
                result_data.get("message", "<missing>"),
                image_path,
            )
            return GenerationResponse(
                success=False,
                status="PipelineError",
                message=tr(
                    "generation_worker_failed",
                    "Die Generierung konnte nicht abgeschlossen werden. Details wurden protokolliert.",
                ),
                model_name=params.model_name
            )

    def _execute_generation_physical(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """
        Runs the physical pipeline inside the virtual environment.
        """
        model_name = job_data.get("model_name", "controlnet_canny_qnn")
        logger.info(f"Starting physical ControlNet generation for model '{model_name}'")

        # Resolve paths
        from controllers.model_repository import ModelRepository
        repo = ModelRepository()
        model_meta = repo.get_model(model_name)
        if model_meta and model_meta.get("path"):
            model_dir = Path(model_meta["path"])
        else:
            model_dir = Path(r"C:\SnapdragonAI\temp\controlnet_canny_gate\controlnet_canny-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite")

        # Validation checks
        metadata_path = model_dir / "metadata.json"
        if not metadata_path.exists():
            return {
                "success": False,
                "message": f"Modellartefakt fehlt: metadata.json unter '{model_dir}'",
                "metadata": {}
            }

        for name in ("text_encoder.onnx", "text_encoder_qairt_context.bin",
                     "controlnet.onnx", "controlnet_qairt_context.bin",
                     "unet.onnx", "unet_qairt_context.bin",
                     "vae.onnx", "vae_qairt_context.bin"):
            if not (model_dir / name).exists():
                return {
                    "success": False,
                    "message": f"Modellartefakt fehlt: {name} unter '{model_dir}'",
                    "metadata": {}
                }

        # Check input image path
        input_image_path = job_data.get("input_image_path")
        if not input_image_path or not Path(input_image_path).exists():
            return {
                "success": False,
                "message": f"Eingabebild für ControlNet fehlt oder ist ungültig: '{input_image_path}'",
                "metadata": {}
            }

        temp_dir = Path(r"C:\SnapdragonAI\temp\controlnet_canny_gate")
        temp_dir.mkdir(parents=True, exist_ok=True)

        t_pipeline_start = time.time()
        sessions_to_close: list[Any] = []
        try:
            # 1. Setup Sessions
            text_encoder_sess, controlnet_sess, unet_sess, vae_sess, provider_diagnostics = self._setup_sessions(model_dir, temp_dir)
            sessions_to_close = [text_encoder_sess, controlnet_sess, unet_sess, vae_sess]

            # 2. Tokenize and Embed
            vocab_path = model_dir / "tokenizer" / "vocab.json"
            if not vocab_path.exists():
                vocab_path = Path(r"C:\SnapdragonAI\temp\stable_diffusion_v1_5_qnn_inspection\stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite\tokenizer\vocab.json")
            merges_path = model_dir / "tokenizer" / "merges.txt"
            if not merges_path.exists():
                merges_path = Path(r"C:\SnapdragonAI\temp\stable_diffusion_v1_5_qnn_inspection\stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite\tokenizer\merges.txt")

            tokenizer = SimpleCLIPTokenizer(vocab_path, merges_path)

            prompt = job_data.get("prompt", "")
            negative_prompt = _resolve_negative_prompt(job_data)

            print("Tokenizing prompt", flush=True)
            cond_tokens = tokenizer.tokenize_prompt(prompt)
            uncond_tokens = tokenizer.tokenize_prompt(negative_prompt)

            cond_arr = np.array([cond_tokens], dtype=np.int32)
            uncond_arr = np.array([uncond_tokens], dtype=np.int32)

            t_infer_start = time.perf_counter()
            cond_emb_q = text_encoder_sess.run(["text_embedding"], {"tokens": cond_arr})[0]
            uncond_emb_q = text_encoder_sess.run(["text_embedding"], {"tokens": uncond_arr})[0]
            t_text_encoder_ms = (time.perf_counter() - t_infer_start) * 1000.0

            # 3. Read metadata.json for quantization params
            with open(model_dir / "metadata.json", "r") as f:
                meta = json.load(f)
            files_meta = meta["model_files"]

            def get_quant_params(model_name, tensor_name, is_input=True):
                model_meta = files_meta[model_name]
                group = "inputs" if is_input else "outputs"
                params = model_meta[group][tensor_name]["quantization_parameters"]
                return params["scale"], params["zero_point"]

            def quantize_tensor(arr, scale, zp):
                return np.clip(np.round(arr / scale) + zp, 0, 65535).astype(np.uint16)

            clipped_low_acc = 0
            clipped_high_acc = 0
            total_elements_acc = 0

            def dequantize_tensor(arr, scale, zp):
                return (arr.astype(np.float32) - zp) * scale

            def requantize_tensor(arr_q, scale_from, zp_from, scale_to, zp_to, factor=1.0):
                nonlocal clipped_low_acc, clipped_high_acc, total_elements_acc
                arr_f = dequantize_tensor(arr_q, scale_from, zp_from)
                if factor != 1.0:
                    arr_f = arr_f * factor
                arr_q_to = np.round(arr_f / scale_to) + zp_to
                clipped_low_acc += np.sum(arr_q_to < 0)
                clipped_high_acc += np.sum(arr_q_to > 65535)
                total_elements_acc += arr_q_to.size
                return np.clip(arr_q_to, 0, 65535).astype(np.uint16)


            # 4. Canny Edge Preprocessing (CPU)
            print("Computing Canny edge image...", flush=True)
            low_threshold = int(job_data.get("canny_low_threshold", 50))
            high_threshold = int(job_data.get("canny_high_threshold", 150))
            conditioning_scale = float(job_data.get("controlnet_conditioning_scale", 1.0))
            canny_edges = canny_edge_detector(input_image_path, low_threshold=low_threshold, high_threshold=high_threshold)

            
            # Format image condition for ControlNet
            canny_edges_f = canny_edges.astype(np.float32) / 255.0
            canny_rgb_f = np.stack([canny_edges_f, canny_edges_f, canny_edges_f], axis=-1)
            canny_rgb_batch_f = np.expand_dims(canny_rgb_f, axis=0)

            scale_cond, zp_cond = get_quant_params("controlnet.onnx", "image_cond", is_input=True)
            canny_quant = quantize_tensor(canny_rgb_batch_f, scale_cond, zp_cond)

            # 5. Denoising Setup
            steps = int(job_data.get("steps", 20))
            seed = job_data.get("seed", -1)
            if seed < 0:
                seed = int(time.time()) % 100000
            
            rng = np.random.default_rng(seed=seed)
            latents = rng.standard_normal((1, 64, 64, 4), dtype=np.float32)

            scheduler = DDIMScheduler()
            scheduler.set_timesteps(steps)
            step_ratio = 1000 // steps

            scale_text_enc_out, zp_text_enc_out = get_quant_params("text_encoder.onnx", "text_embedding", is_input=False)
            scale_lat_cn, zp_lat_cn = get_quant_params("controlnet.onnx", "latent", is_input=True)
            scale_t_cn, zp_t_cn = get_quant_params("controlnet.onnx", "timestep", is_input=True)
            scale_text_cn, zp_text_cn = get_quant_params("controlnet.onnx", "text_emb", is_input=True)

            scale_lat_unet, zp_lat_unet = get_quant_params("unet.onnx", "latent", is_input=True)
            scale_t_unet, zp_t_unet = get_quant_params("unet.onnx", "timestep", is_input=True)
            scale_text_unet, zp_text_unet = get_quant_params("unet.onnx", "text_emb", is_input=True)

            scale_unet_out, zp_unet_out = get_quant_params("unet.onnx", "output_latent", is_input=False)

            cond_emb_cn = requantize_tensor(cond_emb_q, scale_text_enc_out, zp_text_enc_out, scale_text_cn, zp_text_cn)
            cond_emb_unet = requantize_tensor(cond_emb_q, scale_text_enc_out, zp_text_enc_out, scale_text_unet, zp_text_unet)
            uncond_emb_unet = requantize_tensor(uncond_emb_q, scale_text_enc_out, zp_text_enc_out, scale_text_unet, zp_text_unet)

            # 6. Denoising Loop
            print("Generating on Qualcomm Hexagon HTP", flush=True)
            unet_step_times = []
            for step_idx, t_val in enumerate(scheduler.timesteps):
                t0 = time.perf_counter()
                print(f"Step {step_idx+1}/{steps}: Timestep={t_val}", flush=True)

                latent_quant_cn = quantize_tensor(latents, scale_lat_cn, zp_lat_cn)
                t_quant_cn = np.clip(np.round(t_val / scale_t_cn) + zp_t_cn, 0, 65535).astype(np.uint16)
                t_arr_cn = np.array([[t_quant_cn]], dtype=np.uint16)

                # Run ControlNet (single pass)
                controlnet_inputs_cond = {
                    "latent": latent_quant_cn,
                    "timestep": t_arr_cn,
                    "text_emb": cond_emb_cn,
                    "image_cond": canny_quant
                }
                controlnet_outputs_cond = controlnet_sess.run(None, controlnet_inputs_cond)
                output_names_cn = [out.name for out in controlnet_sess.get_outputs()]
                cn_outs_cond_dict = dict(zip(output_names_cn, controlnet_outputs_cond))

                # Prepare UNet inputs
                latent_quant_unet = quantize_tensor(latents, scale_lat_unet, zp_lat_unet)
                t_quant_unet = np.clip(np.round(t_val / scale_t_unet) + zp_t_unet, 0, 65535).astype(np.uint16)
                t_arr_unet = np.array([[t_quant_unet]], dtype=np.uint16)

                unet_inputs_cond = {
                    "latent": latent_quant_unet,
                    "timestep": t_arr_unet,
                    "text_emb": cond_emb_unet
                }
                unet_inputs_uncond = {
                    "latent": latent_quant_unet,
                    "timestep": t_arr_unet,
                    "text_emb": uncond_emb_unet
                }

                for idx in range(12):
                    cn_out_name = f"down_block_{idx}"
                    unet_in_name = f"controlnet_downblock{idx}"
                    scale_cn_out, zp_cn_out = get_quant_params("controlnet.onnx", cn_out_name, is_input=False)
                    scale_unet_in, zp_unet_in = get_quant_params("unet.onnx", unet_in_name, is_input=True)
                    q_val = requantize_tensor(cn_outs_cond_dict[cn_out_name], scale_cn_out, zp_cn_out, scale_unet_in, zp_unet_in, factor=conditioning_scale)
                    unet_inputs_cond[unet_in_name] = q_val
                    unet_inputs_uncond[unet_in_name] = q_val

                scale_cn_mid, zp_cn_mid = get_quant_params("controlnet.onnx", "mid_block", is_input=False)
                scale_unet_mid, zp_unet_mid = get_quant_params("unet.onnx", "controlnet_midblock", is_input=True)
                q_mid = requantize_tensor(cn_outs_cond_dict["mid_block"], scale_cn_mid, zp_cn_mid, scale_unet_mid, zp_unet_mid, factor=conditioning_scale)
                unet_inputs_cond["controlnet_midblock"] = q_mid
                unet_inputs_uncond["controlnet_midblock"] = q_mid


                # Run UNet
                t_unet_start = time.perf_counter()
                out_cond_q = unet_sess.run(["output_latent"], unet_inputs_cond)[0]
                out_uncond_q = unet_sess.run(["output_latent"], unet_inputs_uncond)[0]
                unet_step_times.append((time.perf_counter() - t_unet_start) * 1000.0)

                # Dequantize noise predictions
                noise_pred_cond = dequantize_tensor(out_cond_q, scale_unet_out, zp_unet_out)
                noise_pred_uncond = dequantize_tensor(out_uncond_q, scale_unet_out, zp_unet_out)

                # Classifier Free Guidance
                cfg = float(job_data.get("cfg_scale", 7.5))
                if cfg < 1.0:
                    cfg = 7.5
                model_output = noise_pred_uncond + cfg * (noise_pred_cond - noise_pred_uncond)

                # Scheduler Step
                latents = scheduler.step(model_output, int(t_val), latents, step_ratio)

            t_unet_total_ms = sum(unet_step_times)

            # 7. VAE Decoder
            print("Decoding image on HTP", flush=True)
            scale_vae_in, zp_vae_in = get_quant_params("vae.onnx", "latent", is_input=True)
            vae_latent_quant = quantize_tensor(latents, scale_vae_in, zp_vae_in)

            t_vae_start = time.perf_counter()
            image_quant = vae_sess.run(["image"], {"latent": vae_latent_quant})[0]
            t_vae_ms = (time.perf_counter() - t_vae_start) * 1000.0

            scale_vae_out, zp_vae_out = get_quant_params("vae.onnx", "image", is_input=False)
            image_float = dequantize_tensor(image_quant, scale_vae_out, zp_vae_out)
            image_rgb = np.clip(image_float[0] * 255.0, 0, 255).astype(np.uint8)

            # 8. Save Images using Pillow
            print("Saving image and inputs", flush=True)
            from PIL import Image
            out_img = Image.fromarray(image_rgb)
            canny_img = Image.fromarray(canny_edges)

            output_dir = Path(job_data.get("output_directory", "output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            prefix = job_data.get("output_prefix", "controlnet_canny")
            timestamp = int(time.time())

            # Output filenames
            filename_output = f"{prefix}_{timestamp}_{seed}_output.png"
            filename_canny = f"{prefix}_{timestamp}_{seed}_canny.png"
            filename_input = f"{prefix}_{timestamp}_{seed}_input.png"
            filename_contact = f"{prefix}_{timestamp}_{seed}_contact.png"

            output_dest_path = output_dir / filename_output
            canny_dest_path = output_dir / filename_canny
            input_dest_path = output_dir / filename_input
            contact_dest_path = output_dir / filename_contact

            # Save generated result, canny edge image, and copy input image
            out_img.save(output_dest_path, format="PNG")
            canny_img.save(canny_dest_path, format="PNG")
            shutil.copy2(input_image_path, input_dest_path)

            # Save contact sheet (Eingang, Canny, Ergebnis)
            img_in = preprocess_image_aspect_ratio(Image.open(input_image_path).convert("RGB"), (512, 512))
            img_canny_rgb = canny_img.convert("RGB")
            img_out_res = out_img

            contact = Image.new("RGB", (1536, 512))
            contact.paste(img_in, (0, 0))
            contact.paste(img_canny_rgb, (512, 0))
            contact.paste(img_out_res, (1024, 0))
            contact.save(contact_dest_path, format="PNG")

            total_duration = time.time() - t_pipeline_start
            response_metadata = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "model": model_name,
                "model_id": model_name,
                "model_version": "0.58.0-qnn",
                "backend": "Qualcomm ControlNet Canny (HTP V73)",
                "device": "Qualcomm Hexagon HTP V73",
                "seed": seed,
                "canny_low_threshold": low_threshold,
                "canny_high_threshold": high_threshold,
                "controlnet_conditioning_scale": conditioning_scale,
                "width": 512,

                "height": 512,
                "steps": steps,
                "cfg": cfg,
                "sampler": "DDIM",
                "scheduler": "DDIMScheduler",
                "prediction_type": "epsilon",
                "timesteps": scheduler.timesteps.tolist(),
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "qnn_htp": "V73",
                "cpu_fallback": False,
                "git_commit": _read_git_commit(),
                "backend_version": "2.45",
                "runtime_version": provider_diagnostics["ort_version"],
                "tokenizer_version": "CLIPTokenizer/SD1.5",
                "scheduler_version": "DDIMScheduler",
                "qairt_version": "2.45.0.260326154327",
                "total_runtime_seconds": total_duration,
                "timings": {
                    "text_encoder_ms": t_text_encoder_ms,
                    "unet_total_ms": t_unet_total_ms,
                    "unet_step_avg_ms": np.mean(unet_step_times),
                    "vae_ms": t_vae_ms
                },
                "provider_diagnostics": provider_diagnostics,
                "qnn_htp_verified": True,
                "cpu_fallback_used": False,
                "quantization_diagnostics": {
                    "total_elements": int(total_elements_acc),
                    "clipped_to_zero": int(clipped_low_acc),
                    "clipped_to_max": int(clipped_high_acc),
                    "saturation_percentage": float(clipped_low_acc + clipped_high_acc) / float(total_elements_acc) * 100.0 if total_elements_acc > 0 else 0.0
                },
                "paths": {

                    "input_image": str(input_dest_path),
                    "canny_image": str(canny_dest_path),
                    "output_image": str(output_dest_path),
                    "contact_sheet": str(contact_dest_path)
                }
            }

            metadata_path = output_dest_path.with_suffix(".json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(response_metadata, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": "Qualcomm ControlNet Canny QNN image generation completed successfully.",
                "image_path": str(output_dest_path),
                "generation_time": total_duration,
                "metadata": response_metadata
            }

        except Exception as e:
            logger.exception("Pipeline execution failed")
            return {
                "success": False,
                "message": f"End-to-End Pipeline fehlgeschlagen: {e}",
                "metadata": {}
            }
        finally:
            for session in sessions_to_close:
                try:
                    session.end_profiling()
                except Exception:
                    pass
            sessions_to_close.clear()


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                job_data = json.load(f)
                
            backend = ControlNetCannyQnnBackend()
            result = backend._execute_generation_physical(job_data)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            sys.exit(0)
        except Exception as err:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"success": False, "message": str(err)}, f, indent=2)
            sys.exit(1)
