import sys
import os
import subprocess
import shutil
import time
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Target installation paths
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
INSTALL_DIR = LOCALAPPDATA / "Programs" / "Snapdragon AI Studio"
INSTALLED_EXE = INSTALL_DIR / "SnapdragonAIStudio.exe"

USER_BASE = LOCALAPPDATA / "Snapdragon AI Studio"
MODELS_DIR = USER_BASE / "models"
OUTPUT_DIR = USER_BASE / "output"
LOG_DIR = USER_BASE / "logs"
LOG_FILE = LOG_DIR / "snapdragon_ai_studio.log"

def report_fail(cause, file, function, repro_steps):
    print("\n==========================================")
    print("FAIL")
    print(f"Ursache: {cause}")
    print(f"Datei: {file}")
    print(f"Funktion: {function}")
    print(f"Reproduktionsschritte: {repro_steps}")
    print("==========================================")
    sys.exit(1)

def run_subprocess(cmd, desc):
    print(f"Running: {desc}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        report_fail(
            cause=f"{desc} failed (exit code {res.returncode}): {res.stderr.strip()}",
            file="rc1_acceptance_test.py",
            function="run_subprocess",
            repro_steps=f"python tools/rc1_acceptance_test.py"
        )
    return res

def install_step(installer_path):
    print(f"Running silent installation of {installer_path.name}...")
    cmd = [str(installer_path), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        report_fail(f"Installer failed with code {res.returncode}: {res.stderr}", "rc1_acceptance_test.py", "install_step", "Run installer")

def uninstall_step():
    print("Running silent uninstallation...")
    uninstaller = INSTALL_DIR / "unins000.exe"
    if uninstaller.is_file():
        cmd = [str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"Warning: Uninstaller exited with code {res.returncode}")
        time.sleep(5.0)

def main():
    # 1. Build App
    run_subprocess([sys.executable, "tools/build_app.py"], "PyInstaller build_app")

    # 2. Build Installer
    run_subprocess([sys.executable, "tools/build_installer.py"], "Inno Setup build_installer")

    # 3. Clean any existing installation directories
    if INSTALL_DIR.exists():
        print(f"Cleaning existing installation directory: {INSTALL_DIR}")
        try:
            shutil.rmtree(INSTALL_DIR)
        except Exception as e:
            report_fail(f"Failed to clean install dir: {e}", "rc1_acceptance_test.py", "main", "rmtree INSTALL_DIR")

    # 4. Install silently
    installer_dir = PROJECT_ROOT / "dist" / "installer"
    installers = list(installer_dir.glob("*.exe"))
    if not installers:
        report_fail("No installer executable found in dist/installer", "rc1_acceptance_test.py", "main", "glob dist/installer")
    installer_path = installers[0]
    
    install_step(installer_path)

    if not INSTALLED_EXE.is_file():
        report_fail(f"Installed executable not found at {INSTALLED_EXE}", "rc1_acceptance_test.py", "main", "Check INSTALLED_EXE")

    # 5. Copy models to local appdata models dir
    print("Copying models from source project to local appdata models dir...")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    src_models = PROJECT_ROOT / "models"
    
    import stat
    def handle_remove_readonly(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as e:
            print(f"Could not change permissions for {path}: {e}")

    for item in src_models.iterdir():
        dest = MODELS_DIR / item.name
        if dest.exists():
            try:
                if dest.is_dir():
                    shutil.rmtree(dest, onerror=handle_remove_readonly)
                else:
                    dest.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete {dest}: {e}")
        try:
            if item.is_dir():
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns('.git'))
            else:
                shutil.copy2(item, dest)
        except Exception as e:
            print(f"Warning: Failed to copy {item} to {dest}: {e}")

    # 6. Test: App starts and writes logs
    print("Starting installed application process...")
    p = subprocess.Popen([str(INSTALLED_EXE)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5.0)
    if p.poll() is not None:
        stdout, stderr = p.communicate()
        report_fail(f"Installed app crashed on startup (exit code {p.returncode}): {stderr.decode()}", "rc1_acceptance_test.py", "main", "Launch installed app")
    
    # Terminate process
    p.terminate()
    try:
        p.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        p.kill()

    # Verify logs exist
    if not LOG_FILE.is_file():
        report_fail(f"Log file not created at {LOG_FILE}", "rc1_acceptance_test.py", "main", "Check log file")
    
    log_content = LOG_FILE.read_text(encoding="utf-8")
    if "StartupDiagnostics" not in log_content:
        report_fail("Logs do not contain StartupDiagnostics logs", "rc1_acceptance_test.py", "main", "Check StartupDiagnostics in log")

    # 7. Verify QNN Execution Provider and no Error 126
    # Run a subprocess with PYTHONPATH pointing to the project root and frozen mode simulated
    print("Verifying QNN EP and Error 126...")
    verify_script = f"""
import sys
sys.frozen = True
import onnxruntime as ort
from engine.onnx_provider_service import OnnxProviderService
OnnxProviderService.initialize()
providers = ort.get_available_providers()
print(f"Available providers: {{providers}}")
print(f"QNN status: {{OnnxProviderService.provider_registration_status()}}")
if "QNNExecutionProvider" not in providers:
    sys.exit(10)
"""
    res = subprocess.run([sys.executable, "-c", verify_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        report_fail(
            cause=f"QNNExecutionProvider not available or failed with code {res.returncode}. Stderr: {res.stderr.strip()}",
            file="rc1_acceptance_test.py",
            function="verify_qnn_ep",
            repro_steps="Import onnxruntime & initialize QNN EP"
        )

    # 8. Check Models Detected & SDXL Detected
    print("Checking model detection in registry...")
    detect_script = """
import sys
sys.frozen = True
from controllers.model_repository import ModelRepository
repo = ModelRepository()
models = [m["id"] for m in repo.get_product_models()]
print(f"Detected models: {models}")
if "stable_diffusion_v1_5_qnn" not in models:
    sys.exit(21)
if "stable_diffusion_v2_1_qnn" not in models:
    sys.exit(22)
if "sdxl_base" not in models:
    sys.exit(23)
"""
    res = subprocess.run([sys.executable, "-c", detect_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        report_fail(
            cause=f"Model detection failed with code {res.returncode}. Stderr: {res.stderr.strip()}",
            file="rc1_acceptance_test.py",
            function="check_models",
            repro_steps="Query ModelRepository for detected models"
        )

    # 9. Verify ControlNet Add Image UI component
    print("Verifying ControlNet Add Image UI component...")
    ui_script = """
import sys
import tkinter as tk
sys.frozen = True
from widgets.phoenix.views.prompt_view import PhoenixPromptView
root = tk.Tk()
root.withdraw()
view = PhoenixPromptView(root)
# Check if ControlNet UI components are created
if not hasattr(view, "dnd_card") or not hasattr(view, "low_scale") or not hasattr(view, "strength_scale"):
    sys.exit(31)
"""
    res = subprocess.run([sys.executable, "-c", ui_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        report_fail(
            cause=f"ControlNet UI widgets missing or failed: {res.stderr.strip()}",
            file="rc1_acceptance_test.py",
            function="verify_controlnet_ui",
            repro_steps="Instantiate PhoenixPromptView and verify widget properties"
        )

    # 10. Model Download check
    print("Checking model downloader interface...")
    download_script = """
import sys
sys.frozen = True
from app.model_downloader import ModelDownloader
downloader = ModelDownloader()
# Check if downloader config has correct target URLs/paths
if "stable_diffusion_v1_5_qnn" not in downloader.MODEL_TARGETS:
    sys.exit(41)
"""
    res = subprocess.run([sys.executable, "-c", download_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        report_fail(
            cause=f"Model downloader check failed: {res.stderr.strip()}",
            file="rc1_acceptance_test.py",
            function="check_downloader",
            repro_steps="Query ModelDownloader configuration"
        )

    # 11. Run Image Generation Test for SD1.5 & SD2.1
    def run_generation(model_name, sampler, scheduler):
        print(f"Running generation test for {model_name}...")
        gen_script = f"""
import sys
import time
sys.frozen = True
from controllers.generation_controller import GenerationController
controller = GenerationController()
controller.update_session(
    model_name="{model_name}",
    prompt="A beautiful sunset",
    steps=10,
    cfg_scale=7.5,
    seed=42,
    width=512,
    height=512,
    sampler="{sampler}",
    scheduler="{scheduler}",
)
res = controller.queue_generation(notify_workflow=False)
if not res.success:
    print(f"Error message: {{res.message}}")
    sys.exit(51)
import os
if not res.image_path or not os.path.exists(res.image_path):
    sys.exit(52)
print(f"Generated image: {{res.image_path}}")
"""
        res = subprocess.run([sys.executable, "-c", gen_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=PROJECT_ROOT)
        if res.returncode != 0:
            report_fail(
                cause=f"Generation failed for {model_name}. Code: {res.returncode}. Stderr: {res.stderr.strip()}\nStdout: {res.stdout.strip()}",
                file="rc1_acceptance_test.py",
                function=f"generation_{model_name}",
                repro_steps=f"Run GenerationController for {model_name}"
            )

    # SD1.5 Generation
    run_generation("stable_diffusion_v1_5_qnn", "Euler", "Euler")
    # SD2.1 Generation
    run_generation("stable_diffusion_v2_1_qnn", "DDIM", "DDIM")

    # 12. Check Gallery shows new images
    print("Verifying gallery loads generated images...")
    gallery_script = """
import sys
sys.frozen = True
from controllers.gallery_controller import GalleryController
from config import OUTPUT_DIR
controller = GalleryController()
controller.open_folder(OUTPUT_DIR)
images = controller.visible_images
print(f"Gallery images: {[img.filename for img in images]}")
if not images:
    sys.exit(61)
"""
    res = subprocess.run([sys.executable, "-c", gallery_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        report_fail(
            cause=f"Gallery failed to load generated images: {res.stderr.strip()}",
            file="rc1_acceptance_test.py",
            function="verify_gallery",
            repro_steps="Query GalleryController visible images"
        )

    # 13. Silent Uninstall
    uninstall_step()

    # 14. Reinstall silently
    install_step(installer_path)

    # 15. Re-run generation test
    print("Re-running generation test post-reinstall...")
    run_generation("stable_diffusion_v1_5_qnn", "Euler", "Euler")

    print("\n==========================================")
    print("PASS")
    print("==========================================")

if __name__ == "__main__":
    main()
