import os
import subprocess
from pathlib import Path
from config import QNN_BIN, QNN_BACKEND, QNN_LIB_DIR, QNN_BIN_DIR

def run_qnn_context(model_path: Path, input_list: Path, output_dir: Path, log_level: str = "error") -> None:
    model_path = Path(model_path)
    input_list = Path(input_list)
    output_dir = Path(output_dir)
    if not QNN_BIN.exists():
        raise FileNotFoundError(f"qnn-net-run.exe nicht gefunden: {QNN_BIN}")
    if not QNN_BACKEND.exists():
        raise FileNotFoundError(f"QNN Backend nicht gefunden: {QNN_BACKEND}")
    if not model_path.exists():
        raise FileNotFoundError(f"QNN-Modell nicht gefunden: {model_path}")
    if not input_list.exists():
        raise FileNotFoundError(f"input_list.txt nicht gefunden: {input_list}")
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = f"{QNN_LIB_DIR};{QNN_BIN_DIR};" + env.get("PATH", "")
    cmd = [str(QNN_BIN), "--retrieve_context", str(model_path), "--backend", str(QNN_BACKEND),
           "--input_list", str(input_list), "--output_dir", str(output_dir), "--log_level", log_level]
    subprocess.run(cmd, env=env, check=True)
