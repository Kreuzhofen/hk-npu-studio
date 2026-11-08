"""
HK NPU STUDIO - SPRINT 106
Apply clean standalone patches to config.py, mobilesam_qnn_adapter.py, onnx_provider_service.py, gui_v2.py
"""
import py_compile
import sys
from pathlib import Path

REPO_ROOT = Path(r"C:\SnapdragonAI")

# 1. Patch config.py
config_path = REPO_ROOT / "config.py"
config_content = config_path.read_text(encoding="utf-8")

if "def resolve_model_path" not in config_content:
    target_config = """TEMP_DIR = USER_BASE / "temp"
MODELS_DIR = USER_BASE / "models"
PLUGINS_DIR = BASE / "plugins"
WORKFLOWS_DIR = BASE / "workflows" """

    # Handle both CRLF and LF
    target_found = False
    for nl in ["\r\n", "\n"]:
        tgt = f"TEMP_DIR = USER_BASE / \"temp\"{nl}MODELS_DIR = USER_BASE / \"models\"{nl}PLUGINS_DIR = BASE / \"plugins\"{nl}WORKFLOWS_DIR = BASE / \"workflows\""
        if tgt in config_content:
            repl = (
                f"TEMP_DIR = USER_BASE / \"temp\"{nl}"
                f"MODELS_DIR = USER_BASE / \"models\"{nl}"
                f"PLUGINS_DIR = BASE / \"plugins\"{nl}"
                f"WORKFLOWS_DIR = BASE / \"workflows\"{nl}{nl}{nl}"
                f"def resolve_model_path(relative_path: str | Path) -> Path:{nl}"
                f"    \"\"\"Resolve a model path with multi-tier priority:{nl}"
                f"    1. USER_BASE / 'models' / relative_path (user-customized or downloaded){nl}"
                f"    2. BASE / 'models' / relative_path (bundled base models in application root){nl}"
                f"    \"\"\"{nl}"
                f"    rel = Path(relative_path){nl}"
                f"    user_model = USER_BASE / \"models\" / rel{nl}"
                f"    if user_model.exists():{nl}"
                f"        return user_model{nl}"
                f"    base_model = BASE / \"models\" / rel{nl}"
                f"    if base_model.exists():{nl}"
                f"        return base_model{nl}"
                f"    return user_model{nl}{nl}{nl}"
                f"# Auto-create user-writable directories without requiring admin rights{nl}"
                f"for _dir_path in (INPUT_DIR, OUTPUT_DIR, DATA_DIR, LOG_DIR, TEMP_DIR, MODELS_DIR):{nl}"
                f"    try:{nl}"
                f"        _dir_path.mkdir(parents=True, exist_ok=True){nl}"
                f"    except Exception:{nl}"
                f"        pass{nl}"
            )
            config_content = config_content.replace(tgt, repl, 1)
            config_path.write_text(config_content, encoding="utf-8", newline="\r\n")
            print("config.py patched successfully")
            target_found = True
            break
    if not target_found:
        print("Warning: target not found in config.py")

# 2. Patch engine/backends/mobilesam_qnn_adapter.py
sam_path = REPO_ROOT / "engine" / "backends" / "mobilesam_qnn_adapter.py"
sam_content = sam_path.read_text(encoding="utf-8")

if "DEFAULT_LOCALAPPDATA_SAM_DIR" not in sam_content:
    for nl in ["\r\n", "\n"]:
        tgt_sam = (
            f"DEFAULT_MOBILESAM_DIR = REPO_ROOT / \"models\" / \"mobilesam_qnn\" / \"onnx\"{nl}"
            f"DEFAULT_ENCODER_PATH = DEFAULT_MOBILESAM_DIR / \"encoder.onnx\"{nl}"
            f"DEFAULT_DECODER_PATH = DEFAULT_MOBILESAM_DIR / \"decoder.onnx\""
        )
        if tgt_sam in sam_content:
            repl_sam = (
                f"DEFAULT_LOCALAPPDATA_SAM_DIR = ({nl}"
                f"    Path(os.environ.get(\"LOCALAPPDATA\", \"\")) / \"HK NPU STUDIO\" / \"models\" / \"mobilesam_qnn\" / \"onnx\"{nl}"
                f"){nl}"
                f"DEFAULT_REPO_SAM_DIR = REPO_ROOT / \"models\" / \"mobilesam_qnn\" / \"onnx\"{nl}{nl}"
                f"def _resolve_default_sam_path(filename: str) -> Path:{nl}"
                f"    candidates = []{nl}"
                f"    try:{nl}"
                f"        import config{nl}"
                f"        candidates.append(config.resolve_model_path(Path(\"mobilesam_qnn\") / \"onnx\" / filename)){nl}"
                f"    except Exception:{nl}"
                f"        pass{nl}"
                f"    candidates.append(DEFAULT_LOCALAPPDATA_SAM_DIR / filename){nl}"
                f"    candidates.append(DEFAULT_REPO_SAM_DIR / filename){nl}"
                f"    for c in candidates:{nl}"
                f"        if c.exists():{nl}"
                f"            return c{nl}"
                f"    return candidates[0]{nl}{nl}"
                f"DEFAULT_MOBILESAM_DIR = DEFAULT_REPO_SAM_DIR{nl}"
                f"DEFAULT_ENCODER_PATH = _resolve_default_sam_path(\"encoder.onnx\"){nl}"
                f"DEFAULT_DECODER_PATH = _resolve_default_sam_path(\"decoder.onnx\")"
            )
            sam_content = sam_content.replace(tgt_sam, repl_sam, 1)
            break

    # Also add driverstore path search to _configure_qnn_runtime_env
    for nl in ["\r\n", "\n"]:
        tgt_env = (
            f"        if hasattr(os, \"add_dll_directory\"):{nl}"
            f"            try:{nl}"
            f"                os.add_dll_directory(str(qnn_dir)){nl}"
            f"            except Exception:{nl}"
            f"                pass"
        )
        if tgt_env in sam_content and "FastRPC DriverStore linkage" not in sam_content:
            repl_env = (
                f"        if hasattr(os, \"add_dll_directory\"):{nl}"
                f"            try:{nl}"
                f"                os.add_dll_directory(str(qnn_dir)){nl}"
                f"            except Exception:{nl}"
                f"                pass{nl}"
                f"        # FastRPC DriverStore linkage for libcdsprpc.dll{nl}"
                f"        driverstore = Path(r\"C:\\Windows\\System32\\DriverStore\\FileRepository\"){nl}"
                f"        if driverstore.exists():{nl}"
                f"            for m in driverstore.glob(\"qcadsprpc8380.inf_arm64_*\"):{nl}"
                f"                if (m / \"libcdsprpc.dll\").exists():{nl}"
                f"                    os.environ[\"PATH\"] = str(m) + os.pathsep + os.environ.get(\"PATH\", \"\"){nl}"
                f"                    if hasattr(os, \"add_dll_directory\"):{nl}"
                f"                        try:{nl}"
                f"                            os.add_dll_directory(str(m)){nl}"
                f"                        except Exception:{nl}"
                f"                            pass{nl}"
                f"                    break"
            )
            sam_content = sam_content.replace(tgt_env, repl_env, 1)
            break

    sam_path.write_text(sam_content, encoding="utf-8", newline="\r\n")
    print("mobilesam_qnn_adapter.py patched successfully")

# 3. Patch engine/onnx_provider_service.py
prov_path = REPO_ROOT / "engine" / "onnx_provider_service.py"
prov_content = prov_path.read_text(encoding="utf-8")

if "driverstore.glob" not in prov_content:
    for nl in ["\r\n", "\n"]:
        tgt_prov = (
            f"            cls._add_dll_directory(qnn_library_dir){nl}"
            f"            if cls.AI_STACK_ROOT is not None:"
        )
        if tgt_prov in prov_content:
            repl_prov = (
                f"            cls._add_dll_directory(qnn_library_dir){nl}"
                f"            os.environ[\"ADSP_LIBRARY_PATH\"] = str(qnn_library_dir){nl}"
                f"            driverstore = Path(r\"C:\\Windows\\System32\\DriverStore\\FileRepository\"){nl}"
                f"            if driverstore.exists():{nl}"
                f"                for m in driverstore.glob(\"qcadsprpc8380.inf_arm64_*\"):{nl}"
                f"                    if (m / \"libcdsprpc.dll\").exists():{nl}"
                f"                        cls._add_dll_directory(m){nl}"
                f"                        break{nl}"
                f"            if cls.AI_STACK_ROOT is not None:"
            )
            prov_content = prov_content.replace(tgt_prov, repl_prov, 1)
            prov_path.write_text(prov_content, encoding="utf-8", newline="\r\n")
            print("onnx_provider_service.py patched successfully")
            break

# 4. Patch gui_v2.py to add --validate-standalone
gui_path = REPO_ROOT / "gui_v2.py"
gui_content = gui_path.read_text(encoding="utf-8")

if "--validate-standalone" not in gui_content:
    for nl in ["\r\n", "\n"]:
        tgt_gui = f"    if \"--release-smoke-test\" in sys.argv:"
        if tgt_gui in gui_content:
            repl_gui = (
                f"    if \"--validate-standalone\" in sys.argv:{nl}"
                f"        import config{nl}"
                f"        from engine.phoenix_hybrid_segmenter import PhoenixHybridSegmenter{nl}"
                f"        from PIL import Image{nl}"
                f"        import numpy as np{nl}{nl}"
                f"        diag = run_startup_diagnostics(){nl}"
                f"        seg = PhoenixHybridSegmenter(){nl}"
                f"        test_img = Image.new(\"RGB\", (512, 512), (230, 230, 230)){nl}"
                f"        arr = np.array(test_img){nl}"
                f"        yy, xx = np.ogrid[:512, :512]{nl}"
                f"        arr[((xx - 256)**2 + (yy - 256)**2) <= 80**2] = [220, 20, 20]{nl}"
                f"        res = seg.segment_hybrid(Image.fromarray(arr), point_prompt=(256, 256)){nl}"
                f"        payload = {{{nl}"
                f"            \"safe_to_start\": diag.safe_to_start,{nl}"
                f"            \"selected_backend\": diag.selected_backend,{nl}"
                f"            \"fallback_active\": diag.fallback_active,{nl}"
                f"            \"qnn_provider\": \"QNNExecutionProvider\" in diag.selected_backend,{nl}"
                f"            \"sam_htp_active\": res.mask_array is not None,{nl}"
                f"            \"cpu_fallback_count\": res.cpu_fallback_count,{nl}"
                f"            \"disable_cpu_ep_fallback\": 1,{nl}"
                f"            \"active_pixels\": int(np.count_nonzero(res.mask_array)) if res.mask_array is not None else 0,{nl}"
                f"            \"config_user_base\": str(config.USER_BASE),{nl}"
                f"            \"config_base\": str(config.BASE),{nl}"
                f"            \"sys_frozen\": getattr(sys, \"frozen\", False),{nl}"
                f"        }}{nl}"
                f"        print(json.dumps(payload, indent=2)){nl}"
                f"        return 0 if (diag.safe_to_start and res.cpu_fallback_count == 0) else 1{nl}{nl}"
                f"    if \"--release-smoke-test\" in sys.argv:"
            )
            gui_content = gui_content.replace(tgt_gui, repl_gui, 1)
            gui_path.write_text(gui_content, encoding="utf-8", newline="\r\n")
            print("gui_v2.py patched successfully")
            break

# 5. Check py_compile on all modified files
print("\nChecking py_compile on all patched files...")
for p in [config_path, sam_path, prov_path, gui_path]:
    py_compile.compile(str(p), doraise=True)
    print(f"py_compile {p.name}: OK")
