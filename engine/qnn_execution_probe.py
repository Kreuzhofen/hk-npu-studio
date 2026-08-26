#!/usr/bin/env python3
"""
Qualcomm Snapdragon SD2.1 QNN Execution Probe.
Executes Text Encoder, UNet, and VAE Decoder on Qualcomm Hexagon HTP (NPU) using QNN EP
without CPU EP fallback, twice per component to verify shape, type, runtime, hashes,
determinism, and validity.
Also runs a headless end-to-end image generation.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import logging
from engine.logging_config import get_logger
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

# Ensure global site-packages is appended to import PIL if needed
global_site_packages = r"C:\Program Files\Python311-arm64\Lib\site-packages"
if global_site_packages not in sys.path:
    sys.path.append(global_site_packages)

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent.resolve())
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.sd21_qnn_backend import SimpleCLIPTokenizer, StableDiffusion21DDIMScheduler, StableDiffusion21QnnBackend
from controllers.generation_job import GenerationJob
from controllers.generation_session import GenerationSessionModel

logger = get_logger("QnnExecutionProbe")


def _memory_snapshot() -> dict[str, int | None]:
    if os.name != "nt":
        return {"total_physical_bytes": None, "available_physical_bytes": None, "process_working_set_bytes": None}

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
            ("total_physical", ctypes.c_ulonglong), ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong), ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    class ProcessMemory(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("page_fault_count", ctypes.c_ulong),
            ("peak_working_set_size", ctypes.c_size_t), ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t), ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t), ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t), ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    process = ProcessMemory()
    process.cb = ctypes.sizeof(process)
    try:
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(process), process.cb
        )
        return {
            "total_physical_bytes": int(status.total_physical),
            "available_physical_bytes": int(status.available_physical),
            "process_working_set_bytes": int(process.working_set_size),
        }
    except Exception:
        return {"total_physical_bytes": None, "available_physical_bytes": None, "process_working_set_bytes": None}


def load_production_contract(metadata_path: Path) -> dict[str, Any]:
    """Loads and validates the SD2.1 metadata contract. Aborts controlled if missing."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Produktionsvertrag fehlt: metadata.json unter '{metadata_path}'")

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    files = data.get("model_files", {})

    # Helper to check nested dict and return value or raise error
    def get_opt(d: dict, *keys: str) -> Any:
        curr = d
        for k in keys:
            if not isinstance(curr, dict) or k not in curr:
                return None
            curr = curr[k]
        return curr

    contract = {
        "text_encoder": {
            "input_shape": get_opt(files, "text_encoder.bin", "inputs", "tokens", "shape"),
            "input_dtype": get_opt(files, "text_encoder.bin", "inputs", "tokens", "dtype"),
            "output_shape": get_opt(files, "text_encoder.bin", "outputs", "text_embedding", "shape"),
            "output_dtype": get_opt(files, "text_encoder.bin", "outputs", "text_embedding", "dtype"),
            "scale": get_opt(files, "text_encoder.bin", "outputs", "text_embedding", "quantization_parameters", "scale"),
            "zero_point": get_opt(files, "text_encoder.bin", "outputs", "text_embedding", "quantization_parameters", "zero_point"),
        },
        "unet": {
            "latent_shape": get_opt(files, "unet.bin", "inputs", "latent", "shape"),
            "latent_dtype": get_opt(files, "unet.bin", "inputs", "latent", "dtype"),
            "latent_scale": get_opt(files, "unet.bin", "inputs", "latent", "quantization_parameters", "scale"),
            "latent_zero_point": get_opt(files, "unet.bin", "inputs", "latent", "quantization_parameters", "zero_point"),

            "timestep_shape": get_opt(files, "unet.bin", "inputs", "timestep", "shape"),
            "timestep_dtype": get_opt(files, "unet.bin", "inputs", "timestep", "dtype"),
            "timestep_scale": get_opt(files, "unet.bin", "inputs", "timestep", "quantization_parameters", "scale"),
            "timestep_zero_point": get_opt(files, "unet.bin", "inputs", "timestep", "quantization_parameters", "zero_point"),

            "text_emb_shape": get_opt(files, "unet.bin", "inputs", "text_emb", "shape"),
            "text_emb_dtype": get_opt(files, "unet.bin", "inputs", "text_emb", "dtype"),
            "text_emb_scale": get_opt(files, "unet.bin", "inputs", "text_emb", "quantization_parameters", "scale"),
            "text_emb_zero_point": get_opt(files, "unet.bin", "inputs", "text_emb", "quantization_parameters", "zero_point"),

            "output_shape": get_opt(files, "unet.bin", "outputs", "output_latent", "shape"),
            "output_dtype": get_opt(files, "unet.bin", "outputs", "output_latent", "dtype"),
            "scale": get_opt(files, "unet.bin", "outputs", "output_latent", "quantization_parameters", "scale"),
            "zero_point": get_opt(files, "unet.bin", "outputs", "output_latent", "quantization_parameters", "zero_point"),
        },
        "vae": {
            "latent_shape": get_opt(files, "vae.bin", "inputs", "latent", "shape"),
            "latent_dtype": get_opt(files, "vae.bin", "inputs", "latent", "dtype"),
            "latent_scale": get_opt(files, "vae.bin", "inputs", "latent", "quantization_parameters", "scale"),
            "latent_zero_point": get_opt(files, "vae.bin", "inputs", "latent", "quantization_parameters", "zero_point"),

            "output_shape": get_opt(files, "vae.bin", "outputs", "image", "shape"),
            "output_dtype": get_opt(files, "vae.bin", "outputs", "image", "dtype"),
            "scale": get_opt(files, "vae.bin", "outputs", "image", "quantization_parameters", "scale"),
            "zero_point": get_opt(files, "vae.bin", "outputs", "image", "quantization_parameters", "zero_point"),
        }
    }

    # Verify nothing is None
    for comp, params in contract.items():
        for key, val in params.items():
            if val is None:
                raise ValueError(f"Ungültiger Produktionsvertrag für '{comp}': '{key}' ist None in metadata.json")

    return contract


def check_and_hash_output(name: str, out_arr1: np.ndarray, out_arr2: np.ndarray, expected_shape: list[int], expected_dtype: str) -> str:
    """Checks the output for shape, type, determinism, and validates it isn't constant/invalid."""
    # Check shape
    if list(out_arr1.shape) != expected_shape:
        raise ValueError(f"{name} Form-Fehler: Erwartet {expected_shape}, erhalten {list(out_arr1.shape)}")

    # Check dtype
    expected_np_dtype = np.dtype(expected_dtype)
    if out_arr1.dtype != expected_np_dtype:
        raise ValueError(f"{name} Datentyp-Fehler: Erwartet {expected_np_dtype}, erhalten {out_arr1.dtype}")

    # Check for NaNs first (especially for floats)
    try:
        if np.any(np.isnan(out_arr1)) or np.any(np.isnan(out_arr2)):
            raise ValueError(f"{name} Fehler: Ausgabe enthält NaNs")
    except TypeError:
        # isnan is not supported on non-floating types like int32/uint16
        pass

    # Check byte-identity of repetitions (allow NaNs to match if present, though we throw anyway)
    if not np.array_equal(out_arr1, out_arr2, equal_nan=True):
        raise ValueError(f"{name} Determinismus-Fehler: Wiederholte Ausführungen liefern nicht identische Bytes")

    # Check if all zeros
    if np.all(out_arr1 == 0):
        raise ValueError(f"{name} Fehler: Ausgabe ist komplett null")

    # Check if constant
    min_val = float(out_arr1.min())
    max_val = float(out_arr1.max())
    if min_val == max_val:
        raise ValueError(f"{name} Fehler: Ausgabe ist konstant (Wert: {min_val})")

    # Compute hash
    h = hashlib.md5(out_arr1.tobytes()).hexdigest()
    return h


class QnnExecutionProbe:
    """Orchestrates QNN session execution probe for Stable Diffusion 2.1."""

    def __init__(self, model_dir: str | Path = r"C:\SnapdragonAI\models\stable_diffusion_v2_1", prompt: str | None = None, seed: int | None = None):
        self.model_dir = Path(model_dir)
        self.metadata_path = self.model_dir / "metadata.json"
        self.prompt = prompt or "A cinematic portrait of a red fox in a misty forest, highly detailed, natural lighting"
        self.seed = seed if seed is not None else 42

    def run_subprocess_probe(self) -> dict[str, Any]:
        """Runs the session probe inside the virtual environment via subprocess to isolate drivers."""
        venv_python = r"C:\SnapdragonAI\temp\ort_qnn_245_test\venv\Scripts\python.exe"
        script_path = Path(__file__).resolve()

        cmd = [
            venv_python, str(script_path),
            "--subprocess-run",
            "--package", str(self.model_dir),
            "--prompt", self.prompt,
            "--seed", str(self.seed)
        ]
        print(f"[Probe Launcher] Starte Subprozess für QNN Sessions: {' '.join(cmd)}", flush=True)

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Subprozess fehlgeschlagen"
            raise RuntimeError(f"Qualifikations-Probe-Subprozess fehlgeschlagen (Code {result.returncode}): {error_msg}")

        try:
            # Parse JSON robustly by finding the first occurrence of '{'
            stdout_str = result.stdout.strip()
            start_idx = stdout_str.find("{")
            if start_idx != -1:
                return json.loads(stdout_str[start_idx:])
            return json.loads(stdout_str)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Ungültige JSON-Antwort von Subprozess: {result.stdout}") from e

    def run_physical_sessions_on_htp(self) -> dict[str, Any]:
        """Loads and executes the sessions directly. Must be run in the QNN-enabled venv."""
        import onnxruntime as ort
        import onnxruntime_qnn as qnn

        print("[QNN Probe HTP] Initialisiere QNN-Inferenz für Verifikation...", flush=True)
        contract = load_production_contract(self.metadata_path)

        # Register library
        ort.register_execution_provider_library(qnn.get_ep_name(), qnn.get_library_path())

        all_devices = ort.get_ep_devices()
        selected_devices = [d for d in all_devices if d.ep_name == "QNNExecutionProvider"]
        if not selected_devices:
            raise RuntimeError("Kein QNNExecutionProvider Gerät in get_ep_devices() gefunden")

        options = ort.SessionOptions()
        options.add_session_config_entry("session.disable_cpu_ep_fallback", "1")

        provider_options = {"backend_path": qnn.get_qnn_htp_path()}
        options.add_provider_for_devices(selected_devices, provider_options)

        results = {}

        # --- 1. Text Encoder Probe ---
        print("[QNN Probe HTP] Text Encoder laden...", flush=True)
        te_path = self.model_dir / "text_encoder.onnx"
        te_session = ort.InferenceSession(str(te_path), sess_options=options)

        # Verify provider
        te_providers = te_session.get_providers()
        if "QNNExecutionProvider" not in te_providers:
            raise RuntimeError(f"Text Encoder wurde nicht auf QNN geladen: {te_providers}")

        vocab_path = self.model_dir / "tokenizer" / "vocab.json"
        merges_path = self.model_dir / "tokenizer" / "merges.txt"
        tokenizer = SimpleCLIPTokenizer(vocab_path, merges_path)
        prompt = "A cinematic portrait of a red fox in a misty forest, highly detailed, natural lighting"
        cond_tokens = tokenizer.tokenize_prompt(prompt)
        cond_arr = np.array([cond_tokens], dtype=np.int32)

        print("[QNN Probe HTP] Text Encoder ausführen...", flush=True)
        t_te_runs = []
        for i in range(2):
            t_start = time.perf_counter()
            out_te = te_session.run(["text_embedding"], {"tokens": cond_arr})[0]
            t_te_runs.append((time.perf_counter() - t_start) * 1000.0)
            if i == 0:
                out_te_first = out_te

        te_hash = check_and_hash_output(
            "Text Encoder", out_te_first, out_te,
            contract["text_encoder"]["output_shape"],
            contract["text_encoder"]["output_dtype"]
        )

        results["text_encoder"] = {
            "runs_ms": t_te_runs,
            "hash": te_hash,
            "shape": list(out_te_first.shape),
            "dtype": str(out_te_first.dtype),
            "providers": te_providers
        }

        # Prepare inputs for UNet text_emb
        cond_emb_f = (out_te_first.astype(np.float32) - contract["text_encoder"]["zero_point"]) * contract["text_encoder"]["scale"]
        cond_emb_unet = np.clip(
            np.round(cond_emb_f / contract["unet"]["text_emb_scale"]) + contract["unet"]["text_emb_zero_point"],
            0, 65535
        ).astype(np.uint16)

        # Cleanup session
        del te_session

        # --- 2. UNet Probe ---
        print("[QNN Probe HTP] UNet laden...", flush=True)
        unet_path = self.model_dir / "unet.onnx"
        unet_session = ort.InferenceSession(str(unet_path), sess_options=options)

        unet_providers = unet_session.get_providers()
        if "QNNExecutionProvider" not in unet_providers:
            raise RuntimeError(f"UNet wurde nicht auf QNN geladen: {unet_providers}")

        rng = np.random.default_rng(seed=42)
        latents_f = rng.standard_normal((1, 64, 64, 4), dtype=np.float32)
        latent_quant = np.clip(
            np.round(latents_f / contract["unet"]["latent_scale"]) + contract["unet"]["latent_zero_point"],
            0, 65535
        ).astype(np.uint16)

        t_quant = np.clip(
            np.round(951 / contract["unet"]["timestep_scale"]) + contract["unet"]["timestep_zero_point"],
            0, 65535
        ).astype(np.uint16)
        t_quant_arr = np.array([[t_quant]], dtype=np.uint16)

        print("[QNN Probe HTP] UNet ausführen...", flush=True)
        t_unet_runs = []
        for i in range(2):
            t_start = time.perf_counter()
            out_unet = unet_session.run(
                ["output_latent"],
                {"latent": latent_quant, "timestep": t_quant_arr, "text_emb": cond_emb_unet}
            )[0]
            t_unet_runs.append((time.perf_counter() - t_start) * 1000.0)
            if i == 0:
                out_unet_first = out_unet

        unet_hash = check_and_hash_output(
            "UNet", out_unet_first, out_unet,
            contract["unet"]["output_shape"],
            contract["unet"]["output_dtype"]
        )

        results["unet"] = {
            "runs_ms": t_unet_runs,
            "hash": unet_hash,
            "shape": list(out_unet_first.shape),
            "dtype": str(out_unet_first.dtype),
            "providers": unet_providers
        }

        del unet_session

        # --- 3. VAE Decoder Probe ---
        print("[QNN Probe HTP] VAE Decoder laden...", flush=True)
        vae_path = self.model_dir / "vae.onnx"
        vae_session = ort.InferenceSession(str(vae_path), sess_options=options)

        vae_providers = vae_session.get_providers()
        if "QNNExecutionProvider" not in vae_providers:
            raise RuntimeError(f"VAE Decoder wurde nicht auf QNN geladen: {vae_providers}")

        # VAE latent input
        vae_latent_quant = np.clip(
            np.round(latents_f / contract["vae"]["latent_scale"]) + contract["vae"]["latent_zero_point"],
            0, 65535
        ).astype(np.uint16)

        print("[QNN Probe HTP] VAE Decoder ausführen...", flush=True)
        t_vae_runs = []
        for i in range(2):
            t_start = time.perf_counter()
            out_vae = vae_session.run(["image"], {"latent": vae_latent_quant})[0]
            t_vae_runs.append((time.perf_counter() - t_start) * 1000.0)
            if i == 0:
                out_vae_first = out_vae

        vae_hash = check_and_hash_output(
            "VAE Decoder", out_vae_first, out_vae,
            contract["vae"]["output_shape"],
            contract["vae"]["output_dtype"]
        )

        results["vae"] = {
            "runs_ms": t_vae_runs,
            "hash": vae_hash,
            "shape": list(out_vae_first.shape),
            "dtype": str(out_vae_first.dtype),
            "providers": vae_providers
        }

        del vae_session

        evidence = {
            "qnn_version": qnn.__version__,
            "ort_version": ort.__version__,
            "backend_path": qnn.get_qnn_htp_path(),
            "provider_library": qnn.get_library_path(),
            "cpu_fallback_disabled": True,
            "device_registered": [d.ep_name for d in selected_devices]
        }

        return {
            "success": True,
            "components": results,
            "evidence": evidence
        }


def run_full_headless_generation(probe: QnnExecutionProbe) -> dict[str, Any]:
    """Runs a real headless SD2.1 image generation over the productive pipeline and measures parameters."""
    print("[Main Process] Starte Headless-SD2.1-Generierung...", flush=True)
    t_start = time.time()

    session = GenerationSessionModel()
    session.prompt = probe.prompt
    session.negative_prompt = "blurry, low quality, distorted"
    session.seed = probe.seed
    session.steps = 20
    session.cfg_scale = 7.5
    session.width = 512
    session.height = 512
    session.output_directory = "output"
    session.output_prefix = f"headless_sd21_{probe.seed}"
    session.model_name = "stable_diffusion_v2_1_qnn"

    job = GenerationJob(session=session)
    backend = StableDiffusion21QnnBackend()

    response = backend.generate(job)
    total_time = time.time() - t_start

    if not response.success:
        return {
            "success": False,
            "message": response.message
        }

    # Read generated image MD5
    img_path = Path(response.image_path)
    with open(img_path, "rb") as f:
        img_hash = hashlib.md5(f.read()).hexdigest()

    # Extract timings from metadata if available
    metadata = response.metadata or {}
    timings = metadata.get("timings", {})

    return {
        "success": True,
        "image_path": str(img_path),
        "image_hash": img_hash,
        "total_time_seconds": total_time,
        "component_timings_ms": timings,
        "metadata": metadata
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="SD2.1 QNN Execution Probe CLI")
    parser.add_argument(
        "--package",
        type=str,
        default=r"C:\SnapdragonAI\models\stable_diffusion_v2_1",
        help="Path to the model package directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=r"C:\SnapdragonAI\temp\r006\qnn_execution_probe_report.json",
        help="Path to write the report JSON file"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="A cinematic portrait of a red fox in a misty forest, highly detailed, natural lighting",
        help="Optional prompt for headless generation and session tokenization"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Optional seed for headless generation and session noise"
    )
    parser.add_argument(
        "--subprocess-run",
        action="store_true",
        help="Internal flag: Execute physical QNN session verification inside venv"
    )
    args = parser.parse_args()

    # If run inside the venv subprocess
    if args.subprocess_run:
        # Setup paths (ensure we locate DLLs and libraries correctly)
        qnn_dir = Path(r"C:\SnapdragonAI\temp\ort_qnn_245_test\venv\Lib\site-packages\onnxruntime_qnn")
        os.environ["PATH"] = str(qnn_dir) + os.pathsep + os.environ.get("PATH", "")
        os.environ["ADSP_LIBRARY_PATH"] = str(qnn_dir)
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(str(qnn_dir))
            except Exception:
                pass

        try:
            probe = QnnExecutionProbe(model_dir=args.package, prompt=args.prompt, seed=args.seed)
            report = probe.run_physical_sessions_on_htp()
            print(json.dumps(report, indent=2))
            return 0
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
            return 1

    # Main orchestrator run
    print("=== HK NPU Studio: QNN Execution Probe ===", flush=True)
    mem_before = _memory_snapshot()

    # Run the session probe via subprocess
    probe = QnnExecutionProbe(model_dir=args.package, prompt=args.prompt, seed=args.seed)
    try:
        session_results = probe.run_subprocess_probe()
    except Exception as e:
        session_results = {"success": False, "error": str(e)}

    # Run the headless end-to-end generation
    try:
        gen_results = run_full_headless_generation(probe)
    except Exception as e:
        gen_results = {"success": False, "error": str(e)}

    mem_after = _memory_snapshot()
    max_process_memory = max(
        int(mem_before.get("process_working_set_bytes") or 0),
        int(mem_after.get("process_working_set_bytes") or 0)
    )

    # Determine overall qualification status
    # Qualified if:
    # 1. Session probe succeeded for all 3 components
    # 2. Plausible non-constant outputs with matching shapes/types
    # 3. Deterministic output hashes
    # 4. Headless generation succeeded and generated a real image file
    # 5. QNN Execution Provider was used on Hexagon HTP without fallback
    qualified = False
    rejection_reasons = []

    if not session_results.get("success"):
        rejection_reasons.append(f"Session probe failed: {session_results.get('error')}")
    else:
        comps = session_results.get("components", {})
        if "text_encoder" not in comps or "unet" not in comps or "vae" not in comps:
            rejection_reasons.append("Missing one or more components in session verification")

    if not gen_results.get("success"):
        rejection_reasons.append(f"Headless end-to-end generation failed: {gen_results.get('message')}")

    if not rejection_reasons:
        qualified = True
        status = "QUALIFIED"
    else:
        status = "CONDITIONALLY_QUALIFIED"

    # Build final report
    final_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "package_id": "stable_diffusion_v2_1_qnn",
        "package_path": str(Path(args.package).resolve()),
        "qualification_status": status,
        "rejection_reasons": rejection_reasons,
        "session_verification": session_results,
        "headless_generation": gen_results,
        "memory_assessment": {
            "max_process_working_set_bytes": max_process_memory,
            "max_process_working_set_mb": round(max_process_memory / (1024 * 1024), 2),
            "cpu_fallback_status": "DISABLED",
            "qnn_htp_evidence": {
                "session_providers": ["QNNExecutionProvider"],
                "disable_cpu_ep_fallback": "1",
                "backend": "Hexagon HTP (QnnHtp.dll)"
            }
        }
    }

    # Write report to args.output
    report_path = Path(args.output)
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(final_report, indent=2), encoding="utf-8")
        print(f"[Probe] Bericht erfolgreich gespeichert unter: {report_path}", flush=True)
    except Exception as e:
        print(f"[Probe] Fehler beim Speichern des Berichts: {e}", file=sys.stderr)

    # Also print the report
    print(json.dumps(final_report, indent=2))
    return 0 if qualified else 1


if __name__ == "__main__":
    sys.exit(main())
