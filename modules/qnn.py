import subprocess
from pathlib import Path

from engine.realesrgan_qnn_runtime import resolve_realesrgan_qnn_runtime

def run_qnn_context(input_list: Path, output_dir: Path, log_level: str = "error") -> None:
    runtime = resolve_realesrgan_qnn_runtime()
    input_list = Path(input_list)
    output_dir = Path(output_dir)
    if not input_list.exists():
        raise FileNotFoundError(f"input_list.txt nicht gefunden: {input_list}")
    output_dir.mkdir(parents=True, exist_ok=True)
    env = runtime.process_environment()
    cmd = runtime.build_command(input_list, output_dir, log_level)
    subprocess.run(
        cmd,
        env=env,
        cwd=input_list.parent,
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
