from __future__ import annotations

import tkinter as tk
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.i18n import set_language
from dialogs.update_dialog import ApplicationUpdateWorkflow, UpdateDialog
from engine.application_update_service import (
    ApplicationUpdateCheck,
    ApplicationUpdateLaunch,
    ApplicationUpdateManifest,
    ApplicationUpdateStage,
)
from gui.controllers.ui_builder import UIBuilder
from gui.ui_mode import UIMode
from widgets.menu_bar import MenuBar


def update_manifest() -> ApplicationUpdateManifest:
    return ApplicationUpdateManifest(
        version="2.0.0-rc.4",
        architecture="arm64",
        package_url="https://github.test/HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe",
        sha256="a" * 64,
        asset_name="HKNPUStudio-2.0.0-rc.4-ARM64-Setup.exe",
        asset_size=1024,
        release_name="VERSION 2.0 RC4",
    )


class WorkflowService:
    def __init__(self, check, *, stage_success=True, launch_success=True):
        self.check = check
        self.stage_success = stage_success
        self.launch_success = launch_success
        self.stage_calls = 0
        self.launch_calls = 0
        self.cancel_calls = 0

    def fetch_latest_github_release(self):
        return self.check

    def stage_update(self, _manifest, progress_callback=None):
        self.stage_calls += 1
        if progress_callback:
            progress_callback(512, 1024, 50.0)
            progress_callback(1024, 1024, 100.0)
        if not self.stage_success:
            return ApplicationUpdateStage(False, "hash mismatch")
        return ApplicationUpdateStage(True, "ok", Path("verified.exe"))

    def launch_installer(self, _path):
        self.launch_calls += 1
        return ApplicationUpdateLaunch(
            self.launch_success,
            "started" if self.launch_success else "popen failed",
        )

    def cancel_download(self):
        self.cancel_calls += 1


def make_workflow(service):
    states = []
    exits = []
    workflow = ApplicationUpdateWorkflow(
        service,
        on_state=lambda state, payload: states.append((state, payload)),
        exit_app=lambda: exits.append(True),
    )
    return workflow, states, exits


class FakeDialogWidget:
    def __init__(self, *, visible=True, **options):
        self.visible = visible
        self.options = options

    def configure(self, **options):
        self.options.update(options)

    def pack(self, **_options):
        self.visible = True

    def pack_forget(self):
        self.visible = False

    def winfo_manager(self):
        return "pack" if self.visible else ""


class UpdateDialogStateHarness:
    _on_state = UpdateDialog._on_state
    _show_progress = UpdateDialog._show_progress
    _hide_progress = UpdateDialog._hide_progress
    _cancel = UpdateDialog._cancel
    _format_bytes = staticmethod(UpdateDialog._format_bytes)
    _localized_error = staticmethod(UpdateDialog._localized_error)

    def __init__(self):
        self._manifest = None
        self._running = False
        self.status_label = FakeDialogWidget()
        self.details_label = FakeDialogWidget()
        self.notes_label = FakeDialogWidget()
        self.progress = FakeDialogWidget(visible=False)
        self.progress_label = FakeDialogWidget(visible=False)
        self.install_button = FakeDialogWidget(state="disabled")
        self.cancel_button = FakeDialogWidget(text="Cancel")
        self.workflow = SimpleNamespace(cancel=lambda: None)
        self.close_calls = 0

    def close(self):
        self.close_calls += 1


def test_checking_transitions_to_up_to_date():
    workflow, states, exits = make_workflow(
        WorkflowService(ApplicationUpdateCheck(False, "current"))
    )

    workflow.run_check()

    assert [state for state, _ in states] == ["CHECKING", "UP_TO_DATE"]
    assert exits == []


def test_checking_transitions_to_available():
    manifest = update_manifest()
    workflow, states, _exits = make_workflow(
        WorkflowService(ApplicationUpdateCheck(True, "available", manifest))
    )

    workflow.run_check()

    assert [state for state, _ in states] == ["CHECKING", "AVAILABLE"]
    assert states[-1][1]["manifest"] is manifest


def test_up_to_date_state_hides_checking_progress_and_closes():
    set_language("en_US")
    dialog = UpdateDialogStateHarness()
    try:
        dialog._show_progress()
        dialog._on_state("UP_TO_DATE", {})

        assert dialog.status_label.options["text"] == "HK NPU STUDIO is up to date."
        assert "Checking" not in dialog.status_label.options["text"]
        assert dialog.progress.visible is False
        assert dialog.progress_label.visible is False
        assert dialog.install_button.options["state"] == "disabled"
        assert dialog.cancel_button.options["text"] == "Close"

        dialog._cancel()
        assert dialog.close_calls == 1
    finally:
        set_language("de_DE")


def test_checking_and_available_states_keep_expected_controls():
    set_language("en_US")
    dialog = UpdateDialogStateHarness()
    try:
        dialog._on_state("CHECKING", {})
        assert dialog.status_label.options["text"] == "Checking for updates..."
        assert dialog.progress.visible is False

        dialog._on_state("AVAILABLE", {"manifest": update_manifest()})
        assert dialog.status_label.options["text"] == "Update available"
        assert dialog.install_button.options["state"] == "normal"
        assert dialog.cancel_button.options["text"] == "Cancel"
    finally:
        set_language("de_DE")


def test_error_state_hides_running_progress_and_uses_close():
    set_language("en_US")
    dialog = UpdateDialogStateHarness()
    try:
        dialog._show_progress()
        dialog._on_state("ERROR", {"message": "failed", "error_code": "network"})

        assert dialog.progress.visible is False
        assert dialog.progress_label.visible is False
        assert dialog.install_button.options["state"] == "disabled"
        assert dialog.cancel_button.options["text"] == "Close"
    finally:
        set_language("de_DE")


def test_verified_download_progress_launches_then_exits_once():
    manifest = update_manifest()
    service = WorkflowService(ApplicationUpdateCheck(True, "available", manifest))
    workflow, states, exits = make_workflow(service)

    workflow.run_install(manifest)

    state_names = [state for state, _ in states]
    assert "DOWNLOADING" in state_names
    assert "VERIFYING" in state_names
    assert state_names[-1] == "INSTALLER_STARTED"
    assert service.launch_calls == 1
    assert exits == [True]


@pytest.mark.parametrize("error_code", ["network", "rate_limit", "invalid_response", "installer_missing"])
def test_check_errors_keep_application_open(error_code):
    service = WorkflowService(
        ApplicationUpdateCheck(False, "failed", error_code=error_code)
    )
    workflow, states, exits = make_workflow(service)

    workflow.run_check()

    assert states[-1][0] == "ERROR"
    assert service.launch_calls == 0
    assert exits == []


def test_download_or_hash_failure_never_launches_or_exits():
    manifest = update_manifest()
    service = WorkflowService(
        ApplicationUpdateCheck(True, "available", manifest), stage_success=False
    )
    workflow, states, exits = make_workflow(service)

    workflow.run_install(manifest)

    assert states[-1][0] == "ERROR"
    assert service.launch_calls == 0
    assert exits == []


def test_popen_failure_keeps_application_open():
    manifest = update_manifest()
    service = WorkflowService(
        ApplicationUpdateCheck(True, "available", manifest), launch_success=False
    )
    workflow, states, exits = make_workflow(service)

    workflow.run_install(manifest)

    assert states[-1][0] == "ERROR"
    assert service.launch_calls == 1
    assert exits == []


def test_cancel_reaches_download_service_and_prevents_exit():
    manifest = update_manifest()
    service = WorkflowService(ApplicationUpdateCheck(True, "available", manifest))
    workflow, states, exits = make_workflow(service)

    def cancelled_stage(_manifest, progress_callback=None):
        workflow.cancel()
        return ApplicationUpdateStage(False, "cancelled")

    service.stage_update = cancelled_stage
    workflow.run_install(manifest)

    assert service.cancel_calls == 1
    assert states[-1][0] == "ERROR"
    assert exits == []


def test_top_level_update_menu_invokes_callback_once():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(str(error))
    calls = []
    try:
        set_language("en_US")
        root.geometry("1400x60+0+0")
        menu_bar = MenuBar(root, callbacks={"update": lambda: calls.append(True)})
        entries = [
            (index, menu_bar.menu.entrycget(index, "label"))
            for index in range(menu_bar.menu.index("end") + 1)
            if menu_bar.menu.type(index) != "tearoff"
        ]
        labels = [label for _index, label in entries]
        assert labels == ["File", "Studio", "View", "Plugins", "Tools", "Help", "Update"]
        menu_bar.menu.invoke(entries[-1][0])

        root.update()
        assert calls == [True]
    finally:
        root.destroy()
        set_language("de_DE")


def test_phoenix_builder_renders_no_statusbar_and_workspace_fills_window(monkeypatch):
    class PackedWidget:
        def __init__(self, *_args, **_kwargs):
            self.packed = False
            self.pack_options = {}

        def pack(self, **kwargs):
            self.packed = True
            self.pack_options = kwargs

    class Workspace(PackedWidget):
        pass

    class WorkflowController:
        def __init__(self, **_kwargs):
            pass

    import widgets.phoenix.workspace as workspace_module
    import controllers.workflow_controller as workflow_module
    monkeypatch.setattr(workspace_module, "PhoenixWorkspace", Workspace)
    monkeypatch.setattr(workflow_module, "WorkflowController", WorkflowController)
    app = SimpleNamespace(batch_controller=object())

    UIBuilder(app, ui_mode=UIMode.PHOENIX)._build_phoenix_ui()

    assert not hasattr(app, "status_bar")
    assert app.phoenix_workspace.packed is True
    assert app.phoenix_workspace.pack_options == {"fill": "both", "expand": True}


def test_ui_builder_maps_update_to_application_controller_callback(monkeypatch):
    captured = {}
    update_callback = lambda: None

    class CapturingMenuBar:
        def __init__(self, _app, callbacks):
            captured.update(callbacks)

    import gui.controllers.ui_builder as builder_module

    monkeypatch.setattr(builder_module, "MenuBar", CapturingMenuBar)
    no_op = lambda: None
    app = SimpleNamespace(
        application_controller=SimpleNamespace(open_update_dialog=update_callback),
        open_output_dir=no_op,
        open_models_dir=no_op,
        exit_app=no_op,
        clear_cache=no_op,
        hardware_info=no_op,
        toggle_fullscreen=no_op,
        toggle_sidebar=no_op,
        manage_plugins=no_op,
        open_plugins_dir=no_op,
        show_log=no_op,
        open_about_dialog=no_op,
    )

    UIBuilder(app)._build_menu_bar()

    assert captured["update"] is update_callback
