"""Hardware identity contracts without drivers, registry writes or a GUI."""

import ast
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from engine.hardware_manager import HardwareManager


CPU_NAME = "Snapdragon(R) X2 Elite - X2E-88-100 - Qualcomm Oryon(TM) CPU"
GUI_PATH = Path(__file__).resolve().parents[1] / "gui_v2.py"


def registry(value=CPU_NAME):
    mock = MagicMock()
    mock.QueryValueEx.return_value = (value, 1)
    return mock


def test_native_windows_processor_name():
    reg = registry()
    with patch.dict("sys.modules", {"winreg": reg}), patch("platform.system", return_value="Windows"), patch("platform.processor") as fallback:
        assert HardwareManager().get_processor_name() == CPU_NAME
    fallback.assert_not_called()
    reg.OpenKey.assert_called_once_with(
        reg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    )
    reg.QueryValueEx.assert_called_once_with(reg.OpenKey.return_value.__enter__.return_value, "ProcessorNameString")
    reg.OpenKey.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("failure", ["missing", "open", "query"])
def test_registry_failure_uses_platform_processor(failure):
    reg = registry()
    if failure == "open":
        reg.OpenKey.side_effect = OSError("unavailable")
    if failure == "query":
        reg.QueryValueEx.side_effect = OSError("unavailable")
    with patch.dict("sys.modules", {"winreg": None if failure == "missing" else reg}), patch("platform.system", return_value="Windows"), patch("platform.processor", return_value="Fallback CPU"):
        assert HardwareManager().get_processor_name() == "Fallback CPU"


def test_empty_sources_fall_back_to_machine():
    with patch.dict("sys.modules", {"winreg": registry(" ")}), patch("platform.system", return_value="Windows"), patch("platform.processor", return_value=""), patch("platform.machine", return_value="ARM64"):
        assert HardwareManager().get_processor_name() == "ARM64"


def test_fallback_exceptions_never_escape():
    with patch("platform.system", side_effect=RuntimeError()), patch("platform.processor", side_effect=RuntimeError()), patch("platform.machine", side_effect=RuntimeError()):
        assert HardwareManager().get_processor_name() == "Unbekannt"


def test_non_windows_does_not_read_registry():
    reg = registry()
    with patch.dict("sys.modules", {"winreg": reg}), patch("platform.system", return_value="Linux"), patch("platform.processor", return_value="Other CPU"):
        assert HardwareManager().get_processor_name() == "Other CPU"
    reg.OpenKey.assert_not_called()


def test_system_info_uses_central_resolver():
    manager = HardwareManager()
    with patch.object(manager, "get_processor_name", return_value=CPU_NAME) as resolve, patch.object(manager, "get_ram_gb", return_value=16), patch.object(manager, "is_qnn_available", return_value=False):
        assert manager.get_system_info()["processor"] == CPU_NAME
    resolve.assert_called_once()


@pytest.mark.parametrize("sdk,tools,htp,expected", [
    (True, True, "QnnHtp.dll", True),
    (False, True, "QnnHtp.dll", False),
    (True, False, "QnnHtp.dll", False),
    (True, True, None, False),
])
def test_qnn_still_uses_backend_discovery(sdk, tools, htp, expected):
    result = SimpleNamespace(qnn_sdk_found=sdk, qnn_tools_found=tools, qnn_htp_backend_path=htp)
    with patch("engine.hardware_manager.BackendDiscoveryService.discover", return_value=result) as discover:
        assert HardwareManager().is_qnn_available() is expected
    discover.assert_called_once()


def test_qnn_discovery_failure_is_unavailable():
    with patch("engine.hardware_manager.BackendDiscoveryService.discover", side_effect=OSError()):
        assert HardwareManager().is_qnn_available() is False


@pytest.mark.parametrize("available", [True, False])
def test_hardware_dialog_reports_detected_values(available):
    # Execute the actual dialog method without importing/starting the application.
    tree = ast.parse(GUI_PATH.read_text(encoding="utf-8"))
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "hardware_info")
    namespace = {"tr": lambda key, fallback, **values: fallback.format(**values)}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(GUI_PATH), "exec"), namespace)
    with patch.object(HardwareManager, "get_system_info", return_value={"processor": CPU_NAME, "qnn_available": available}), patch("tkinter.messagebox.showinfo") as show:
        namespace["hardware_info"](None)
    body = show.call_args.args[1]
    assert CPU_NAME in body
    assert "CPU fallback" not in body
    if available:
        assert "Qualcomm Hexagon / QNN HTP" in body
        assert "Execution Provider: QNN / HTP" in body
    else:
        assert "HTP" not in body
        assert body.count("Nicht verfügbar") == 2


def test_gui_has_no_fabricated_hardware_literals():
    source = GUI_PATH.read_text(encoding="utf-8")
    assert "Qualcomm Snapdragon X Elite (ARM64)" not in source
    assert "QNNExecutionProvider / CPU fallback" not in source
