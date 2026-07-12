#!/usr/bin/env python3
"""
Qualcomm Stable Diffusion 1.5 QNN Backend.
Subclasses InferenceBackend to run SD1.5 w8a16 precompiled context models on Qualcomm Hexagon HTP.
Utilizes a subprocess worker to isolate QAIRT 2.45.41 from QAIRT 2.47 system drivers.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
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
    sys.path.append(project_root)

from controllers.generation_job import GenerationJob
from engine.generation_response import GenerationResponse
from engine.inference_backend import InferenceBackend

logger = logging.getLogger("StableDiffusion15QnnBackend")


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

# Setup process environment for QNN runtime
ROOT = Path(r"C:\SnapdragonAI\temp\sd15_first_npu_image")
MODEL_DIR = Path(r"C:\SnapdragonAI\temp\stable_diffusion_v1_5_qnn_inspection\stable_diffusion_v1_5-precompiled_qnn_onnx-w8a16-qualcomm_snapdragon_x_elite")
qnn_dir = Path(r"C:\SnapdragonAI\temp\ort_qnn_245_test\venv\Lib\site-packages\onnxruntime_qnn")
os.environ["PATH"] = str(qnn_dir) + os.pathsep + os.environ.get("PATH", "")
os.environ["ADSP_LIBRARY_PATH"] = str(qnn_dir)
if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(str(qnn_dir))
    except Exception:
        pass


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
        self.pat = re.compile(r"""<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|[a-zA-Z]+|[0-9]+|[^a-zA-Z0-9\s]+""", re.IGNORECASE)
        
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


class EulerScheduler:
    def __init__(self, num_train_timesteps: int = 1000, beta_start: float = 0.00085, beta_end: float = 0.012) -> None:
        self.num_train_timesteps = num_train_timesteps
        self.betas = np.linspace(beta_start**0.5, beta_end**0.5, num_train_timesteps, dtype=np.float32)**2
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = np.cumprod(self.alphas, axis=0)
        
    def set_timesteps(self, num_inference_steps: int) -> None:
        step_ratio = self.num_train_timesteps // num_inference_steps
        self.timesteps = (
            np.arange(num_inference_steps) * step_ratio
        ).round()[::-1].astype(np.int32) + 1
        
        sigmas_full = ((1.0 - self.alphas_cumprod) / self.alphas_cumprod) ** 0.5
        sigmas = []
        for t in self.timesteps:
            sigmas.append(sigmas_full[t])
        sigmas.append(0.0)
        self.sigmas = np.array(sigmas, dtype=np.float32)


class StableDiffusion15QnnBackend(InferenceBackend):
    """
    Physical backend executing SD1.5 on Snapdragon HTP NPU via QNN EP.
    """

    def __init__(self) -> None:
        self.tokenizer = None
        self.scheduler = None

    def _setup_sessions(self, model_dir: Path) -> tuple[Any, Any, Any, dict[str, Any]]:
        import onnxruntime as ort
        import onnxruntime_qnn as qnn

        # Introspect ORT and devices
        has_devices_api = hasattr(ort, "get_ep_devices") and hasattr(ort.SessionOptions, "add_provider_for_devices")
        if not has_devices_api:
            raise RuntimeError("ORT does not support required get_ep_devices or add_provider_for_devices APIs")

        print("Preparing Qualcomm QNN runtime", flush=True)
        # 1. Register QNN plugin EP library
        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())
        
        # 2. Get EP devices and choose QNN Execution Provider
        all_devices = ort.get_ep_devices()
        selected_devices = [d for d in all_devices if d.ep_name == "QNNExecutionProvider"]
        if not selected_devices:
            raise RuntimeError("No QNNExecutionProvider devices found in get_ep_devices()")

        # Create session configurations
        options = ort.SessionOptions()
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")
        options.enable_profiling = True
        options.profile_file_prefix = str(ROOT / "onnx_profile")
        
        provider_options = {"backend_path": qnn.get_qnn_htp_path()}
        options.add_provider_for_devices(selected_devices, provider_options)

        print("Loading Text Encoder on HTP", flush=True)
        text_encoder_session = ort.InferenceSession(str(model_dir / "text_encoder.onnx"), sess_options=options)

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

        return text_encoder_session, unet_session, vae_session, provider_diagnostics

    def generate(self, job: GenerationJob) -> GenerationResponse:
        # Main Process Mode: Spawn worker subprocess to isolate QAIRT 2.45
        logger.info("[Main Process] Spawning worker subprocess for SD1.5 QNN...")
        print("[Main Process] Spawning worker subprocess for SD1.5 QNN...")

        # Create temporary json files for communication
        temp_dir = Path(r"C:\SnapdragonAI\temp\sd15_first_npu_image")
        temp_dir.mkdir(parents=True, exist_ok=True)
        job_id_str = str(job.job_id)[:8]
        input_json_path = temp_dir / f"job_input_{job_id_str}.json"
        output_json_path = temp_dir / f"job_output_{job_id_str}.json"

        # Serialize job parameters
        job_data = {
            "prompt": job.session.prompt,
            "negative_prompt": job.session.negative_prompt,
            "seed": job.session.seed,
            "steps": job.session.steps,
            "cfg_scale": job.session.cfg_scale,
            "width": job.session.width,
            "height": job.session.height,
            "output_directory": job.session.output_directory,
            "output_prefix": job.session.output_prefix,
            "model_name": job.session.model_name,
            "job_id": str(job.job_id)
        }

        with open(input_json_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, indent=2)

        # Run subprocess using the venv python executable
        venv_python = r"C:\SnapdragonAI\temp\ort_qnn_245_test\venv\Scripts\python.exe"
        script_path = Path(__file__).resolve()

        import subprocess
        cmd = [
            venv_python,
            str(script_path),
            str(input_json_path),
            str(output_json_path)
        ]

        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Start subprocess and capture stdout/stderr
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Read output in real-time to update status/progress
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line_str = line.strip()
                print(f"[QNN Worker] {line_str}")
                # Log status in prompt view and update job status
                if any(k in line_str for k in ["Preparing", "Loading", "Starting", "Tokenizing", "Running", "Decoding", "Saving", "Step", "Image"]):
                    job.status = line_str
                    
                    # Estimate progress based on steps
                    if "Step " in line_str and "/" in line_str:
                        try:
                            parts = line_str.split("Step ")[1].split(":")[0].split("/")
                            curr = int(parts[0])
                            total = int(parts[1])
                            job.progress = float(curr) / float(total)
                        except Exception:
                            pass

        process.wait()

        # Check if output json exists
        if not output_json_path.exists():
            err_msg = "Subprocess finished but did not write output JSON."
            logger.error(err_msg)
            return GenerationResponse(
                success=False,
                status="PipelineError",
                message=err_msg,
                model_name=job.session.model_name
            )

        with open(output_json_path, "r", encoding="utf-8") as f:
            result_data = json.load(f)

        # Clean up temp files
        try:
            input_json_path.unlink(missing_ok=True)
            output_json_path.unlink(missing_ok=True)
        except Exception:
            pass

        if result_data.get("success"):
            return GenerationResponse(
                success=True,
                status="FINISHED",
                message=result_data.get("message", "Generierung abgeschlossen."),
                image_path=result_data.get("image_path"),
                thumbnail_path=result_data.get("image_path"),
                generation_time=result_data.get("generation_time", 0.0),
                backend_name="Qualcomm Stable Diffusion 1.5 (HTP V73)",
                model_name=job.session.model_name,
                metadata=result_data.get("metadata", {})
            )
        else:
            return GenerationResponse(
                success=False,
                status="PipelineError",
                message=result_data.get("message", "Pipeline fehlgeschlagen."),
                model_name=job.session.model_name
            )

    def _execute_generation_physical(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """
        Runs the physical pipeline inside the virtual environment.
        """
        model_name = job_data.get("model_name", "stable_diffusion_v1_5_qnn")
        logger.info(f"Starting physical generation for model '{model_name}'")

        # Resolve paths
        from controllers.model_repository import ModelRepository
        repo = ModelRepository()
        model_meta = repo.get_model(model_name)
        if model_meta and model_meta.get("path"):
            model_dir = Path(model_meta["path"])
        else:
            model_dir = MODEL_DIR

        # Validation checks
        metadata_path = model_dir / "metadata.json"
        if not metadata_path.exists():
            return {
                "success": False,
                "message": f"Modellartefakt fehlt: metadata.json unter '{model_dir}'",
                "metadata": {}
            }

        for name in ("text_encoder.onnx", "text_encoder_qairt_context.bin",
                     "unet.onnx", "unet_qairt_context.bin",
                     "vae.onnx", "vae_qairt_context.bin"):
            if not (model_dir / name).exists():
                return {
                    "success": False,
                    "message": f"Modellartefakt fehlt: {name} unter '{model_dir}'",
                    "metadata": {}
                }

        vocab_path = model_dir / "tokenizer" / "vocab.json"
        merges_path = model_dir / "tokenizer" / "merges.txt"
        if not vocab_path.exists() or not merges_path.exists():
            return {
                "success": False,
                "message": f"Tokenizer-Ressourcen fehlen unter '{model_dir}/tokenizer'",
                "metadata": {}
            }

        # Force 512x512 resolution for this precompiled model layout
        width = 512
        height = 512
        steps = int(job_data.get("steps", 20))

        t_pipeline_start = time.time()
        try:
            # 1. Setup Sessions
            text_encoder_session, unet_session, vae_session, provider_diagnostics = self._setup_sessions(model_dir)

            # 2. Tokenize and Embed
            tokenizer = SimpleCLIPTokenizer(vocab_path, merges_path)
            
            prompt = job_data.get("prompt", "")
            negative_prompt = str(job_data.get("negative_prompt", ""))

            print("Tokenizing prompt", flush=True)
            cond_tokens = tokenizer.tokenize_prompt(prompt)
            uncond_tokens = tokenizer.tokenize_prompt(negative_prompt)

            cond_arr = np.array([cond_tokens], dtype=np.int32)
            uncond_arr = np.array([uncond_tokens], dtype=np.int32)

            t_infer_start = time.perf_counter()
            cond_emb_q = text_encoder_session.run(["text_embedding"], {"tokens": cond_arr})[0]
            uncond_emb_q = text_encoder_session.run(["text_embedding"], {"tokens": uncond_arr})[0]
            t_text_encoder_ms = (time.perf_counter() - t_infer_start) * 1000.0

            # Dequantize text embeddings to float32
            # Text Encoder: scale=0.0009303585393354297, zero_point=30063
            cond_emb_f = (cond_emb_q.astype(np.float32) - 30063) * 0.0009303585393354297
            uncond_emb_f = (uncond_emb_q.astype(np.float32) - 30063) * 0.0009303585393354297

            # Re-quantize for UNet text_emb input
            # UNet text_emb: scale=0.0009331560577265918, zero_point=30103
            cond_emb_unet = np.clip(np.round(cond_emb_f / 0.0009331560577265918) + 30103, 0, 65535).astype(np.uint16)
            uncond_emb_unet = np.clip(np.round(uncond_emb_f / 0.0009331560577265918) + 30103, 0, 65535).astype(np.uint16)

            # 3. Setup Scheduler & Initial Latents
            scheduler = EulerScheduler()
            scheduler.set_timesteps(steps)

            seed = job_data.get("seed", -1)
            if seed < 0:
                seed = int(time.time()) % 100000
            rng = np.random.default_rng(seed=seed)
            latents = rng.standard_normal((1, 64, 64, 4), dtype=np.float32) * scheduler.sigmas[0]
            initial_latents = latents.copy()

            # 4. Denoising Loop
            print("Generating on Qualcomm Hexagon HTP", flush=True)
            unet_step_times = []
            for step_idx, t in enumerate(scheduler.timesteps):
                sigma = scheduler.sigmas[step_idx]
                next_sigma = scheduler.sigmas[step_idx + 1]

                print(f"Step {step_idx+1}/{steps}: Timestep={t}, Sigma={sigma:.4f}", flush=True)

                # Scale latents for UNet input
                latent_model_input = latents / ((sigma**2 + 1.0)**0.5)

                # Quantize latent input: scale=0.00024176308943424374, zero_point=33983
                latent_quant = np.clip(np.round(latent_model_input / 0.00024176308943424374) + 33983, 0, 65535).astype(np.uint16)

                # Quantize timestep: scale=0.014770733192563057, zero_point=0
                t_quant = np.clip(np.round(t / 0.014770733192563057), 0, 65535).astype(np.uint16)
                t_quant_arr = np.array([[t_quant]], dtype=np.uint16)

                t_unet_start = time.perf_counter()
                out_cond_q = unet_session.run(["output_latent"], {"latent": latent_quant, "timestep": t_quant_arr, "text_emb": cond_emb_unet})[0]
                out_uncond_q = unet_session.run(["output_latent"], {"latent": latent_quant, "timestep": t_quant_arr, "text_emb": uncond_emb_unet})[0]
                unet_step_times.append((time.perf_counter() - t_unet_start) * 1000.0)

                # Dequantize noise predictions: scale=0.0001881735515780747, zero_point=32340
                noise_pred_cond = (out_cond_q.astype(np.float32) - 32340) * 0.0001881735515780747
                noise_pred_uncond = (out_uncond_q.astype(np.float32) - 32340) * 0.0001881735515780747

                # Classifier Free Guidance (Guidance Scale defaults to 7.5 or session cfg_scale)
                cfg = job_data.get("cfg_scale", 7.5)
                if cfg < 1.0:
                    cfg = 7.5
                noise_pred = noise_pred_uncond + cfg * (noise_pred_cond - noise_pred_uncond)

                # Euler step
                dt = next_sigma - sigma
                latents = latents + noise_pred * dt

            t_unet_total_ms = sum(unet_step_times)

            # 5. VAE Decoder
            print("Decoding image on HTP", flush=True)
            latents_vae = latents
            # VAE latent input: scale=0.00034003707696683705, zero_point=34382
            latents_vae_quant = np.clip(np.round(latents_vae / 0.00034003707696683705) + 34382, 0, 65535).astype(np.uint16)

            t_vae_start = time.perf_counter()
            image_quant = vae_session.run(["image"], {"latent": latents_vae_quant})[0]
            t_vae_ms = (time.perf_counter() - t_vae_start) * 1000.0

            # Dequantize VAE output: scale=0.000015259021893143654, zero_point=0
            image_float = image_quant.astype(np.float32) * 0.000015259021893143654
            image_rgb = np.clip(image_float[0] * 255.0, 0, 255).astype(np.uint8)

            # Clean up sessions to release NPU memory
            text_encoder_session.end_profiling()
            unet_session.end_profiling()
            vae_session.end_profiling()
            del text_encoder_session, unet_session, vae_session

            # 6. Save image using Pillow
            print("Saving image", flush=True)
            from PIL import Image
            img = Image.fromarray(image_rgb)

            output_dir = Path(job_data.get("output_directory", "output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            prefix = job_data.get("output_prefix", "generate")
            timestamp = int(time.time())
            filename = f"{prefix}_{timestamp}_{job_data.get('job_id', '')[:8]}.png"
            image_path = output_dir / filename

            img.save(image_path, format="PNG")
            png_size = image_path.stat().st_size

            # Save JSON sidecar
            total_duration = time.time() - t_pipeline_start
            response_metadata = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "model": model_name,
                "backend": "Qualcomm Stable Diffusion 1.5 (HTP V73)",
                "seed": seed,
                "width": width,
                "height": height,
                "steps": steps,
                "cfg": cfg,
                "sampler": "Euler a",
                "scheduler": "EulerScheduler",
                "prediction_type": "epsilon",
                "timesteps": scheduler.timesteps.tolist(),
                "sigmas": scheduler.sigmas.tolist(),
                "latent_scaling": {
                    "initial_noise_sigma": float(scheduler.sigmas[0]),
                    "unet_input": "latents / sqrt(sigma^2 + 1)",
                    "vae_scaling_applied": False,
                },
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "qnn_htp": "V73",
                "cpu_fallback": False,
                "git_commit": _read_git_commit(),
                "backend_version": "2.45",
                "runtime_version": provider_diagnostics["ort_version"],
                "model_version": "1.5.0-qnn",
                "tokenizer_version": "CLIPTokenizer/SD1.5",
                "scheduler_version": "EulerScheduler",
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
                "cpu_fallback_used": False
            }
            response_metadata["tensor_diagnostics"] = [
                _tensor_summary("text_encoder.tokens.conditional", cond_arr),
                _tensor_summary("text_encoder.tokens.unconditional", uncond_arr),
                _tensor_summary("text_encoder.text_embedding.conditional", cond_emb_q),
                _tensor_summary("text_encoder.text_embedding.unconditional", uncond_emb_q),
                _tensor_summary("unet.text_emb.conditional", cond_emb_unet),
                _tensor_summary("unet.text_emb.unconditional", uncond_emb_unet),
                _tensor_summary("unet.latent.initial", initial_latents),
                _tensor_summary("unet.output_latent.conditional.last", out_cond_q),
                _tensor_summary("unet.output_latent.unconditional.last", out_uncond_q),
                _tensor_summary("vae.latent.float", latents_vae),
                _tensor_summary("vae.latent.quantized", latents_vae_quant),
                _tensor_summary("vae.image.quantized", image_quant),
                _tensor_summary("image.float", image_float),
                _tensor_summary("image.rgb_uint8", image_rgb),
            ]

            metadata_path = image_path.with_suffix(".json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(response_metadata, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": "Qualcomm SD1.5 QNN local image generation completed successfully on Hexagon NPU.",
                "image_path": str(image_path),
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


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                job_data = json.load(f)
                
            backend = StableDiffusion15QnnBackend()
            result = backend._execute_generation_physical(job_data)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            sys.exit(0)
        except Exception as err:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"success": False, "message": str(err)}, f, indent=2)
            sys.exit(1)
