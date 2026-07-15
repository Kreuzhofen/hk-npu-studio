from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import json
from pathlib import Path
import subprocess
import time
import tkinter as tk
from typing import Callable

from PIL import Image, ImageTk

from config import BASE, OUTPUT_DIR
from controllers.model_manager_controller import ModelManagerController
from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME


@dataclass(frozen=True)
class LatestGeneration:
    path: Path
    filename: str
    model: str
    resolution: str
    created_at: str


@dataclass(frozen=True)
class HomeSnapshot:
    npu_status: str
    qnn_runtime: str
    onnx_runtime: str
    installed_models: str
    active_model: str
    version: str
    branch: str
    installed_packages: str
    latest_generation: LatestGeneration | None


class PhoenixHomeView(tk.Frame):
    """Real-data control center for the Phoenix workspace."""

    REFRESH_INTERVAL_SECONDS = 5.0

    def __init__(
        self,
        master: tk.Misc,
        controller: object | None = None,
        on_navigate: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(master, bg=PHOENIX_THEME.content_bg)
        self.controller = controller
        self._on_navigate = on_navigate
        self._model_controller = ModelManagerController()
        self._project_branch = self._read_project_branch()
        self._last_refresh_at = 0.0
        self._last_generation_path: Path | None = None
        self._last_generation_photo: ImageTk.PhotoImage | None = None

        self._system_values: dict[str, tk.Label] = {}
        self._project_values: dict[str, tk.Label] = {}

        self._build()
        self.refresh(force=True)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        welcome = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        welcome.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_xl,
            pady=(PHOENIX_THEME.space_xl, PHOENIX_THEME.space_lg),
        )
        tk.Label(
            welcome,
            text="Willkommen",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            welcome,
            text="Snapdragon AI Studio",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, 0))
        tk.Label(
            welcome,
            text="Create. Organize. Review. Evolve.",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).pack(fill="x", pady=(PHOENIX_THEME.space_xs, 0))

        actions = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        actions.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_lg),
        )
        tk.Label(
            actions,
            text="Schnellaktionen",
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, PHOENIX_THEME.space_sm))
        for column in range(4):
            actions.grid_columnconfigure(column, weight=1, uniform="home_actions")

        action_specs = (
            ("🎨", "AI Generate", "prompt"),
            ("🤖", "AI Model Manager", "models"),
            ("📚", "AI Asset Library", "gallery"),
            ("🔍", "Review Workspace", "compare"),
        )
        for column, (icon, title, target) in enumerate(action_specs):
            self._create_action_card(actions, icon, title, target, column)

        status_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        status_host.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_lg),
        )
        status_host.grid_columnconfigure((0, 1), weight=1, uniform="home_status")

        system_card = self._create_section_card(status_host, "Systemstatus")
        system_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, PHOENIX_THEME.space_sm),
        )
        for row, (key, label) in enumerate(
            (
                ("npu", "NPU"),
                ("qnn", "QNN Runtime"),
                ("onnx", "ONNX Runtime"),
                ("models", "Installierte Modelle"),
                ("active", "Aktives Modell"),
            ),
            start=1,
        ):
            self._system_values[key] = self._create_metric_row(system_card, label, row)

        project_card = self._create_section_card(status_host, "Projektstatus")
        project_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_sm, 0),
        )
        for row, (key, label) in enumerate(
            (
                ("version", "Version"),
                ("branch", "Branch"),
                ("packages", "Installierte AI Packages"),
            ),
            start=1,
        ):
            self._project_values[key] = self._create_metric_row(project_card, label, row)

        self._last_card = self._create_section_card(self, "Letzte Generierung")
        self._last_card.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_xl),
        )
        self._last_card.grid_columnconfigure(1, weight=1)
        self._last_preview = tk.Label(
            self._last_card,
            bg=PHOENIX_THEME.card_bg,
            bd=0,
        )
        self._last_preview.grid(
            row=1,
            column=0,
            rowspan=2,
            sticky="nw",
            padx=(PHOENIX_THEME.card_pad_x, PHOENIX_THEME.space_lg),
            pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.card_pad_y),
        )
        self._last_message = tk.Label(
            self._last_card,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
            justify="left",
        )
        self._last_message.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(0, PHOENIX_THEME.card_pad_x),
            pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.space_xs),
        )
        self._last_details = tk.Label(
            self._last_card,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="nw",
            justify="left",
        )
        self._last_details.grid(
            row=2,
            column=1,
            sticky="new",
            padx=(0, PHOENIX_THEME.card_pad_x),
            pady=(0, PHOENIX_THEME.card_pad_y),
        )

    def _create_action_card(
        self,
        parent: tk.Frame,
        icon: str,
        title: str,
        target: str,
        column: int,
    ) -> None:
        card = tk.Frame(
            parent,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
            cursor="hand2",
        )
        card.grid(
            row=1,
            column=column,
            sticky="nsew",
            padx=(
                0 if column == 0 else PHOENIX_THEME.space_sm,
                0 if column == 3 else PHOENIX_THEME.space_sm,
            ),
        )
        icon_label = tk.Label(
            card,
            text=icon,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.accent,
            font=PHOENIX_THEME.font_title,
            cursor="hand2",
        )
        icon_label.pack(anchor="w", padx=PHOENIX_THEME.card_pad_x, pady=(PHOENIX_THEME.card_pad_y, 0))
        title_label = tk.Label(
            card,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
            cursor="hand2",
        )
        title_label.pack(
            fill="x",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.space_sm, PHOENIX_THEME.card_pad_y),
        )

        widgets = (card, icon_label, title_label)

        def set_hover(active: bool) -> None:
            background = PHOENIX_THEME.elevated_bg if active else PHOENIX_THEME.card_bg
            card.configure(
                bg=background,
                highlightbackground=PHOENIX_THEME.accent if active else PHOENIX_THEME.border,
            )
            icon_label.configure(bg=background)
            title_label.configure(bg=background)

        for widget in widgets:
            widget.bind("<Button-1>", lambda _event, destination=target: self._navigate(destination))
            widget.bind("<Enter>", lambda _event: set_hover(True), add="+")
            widget.bind("<Leave>", lambda _event: set_hover(False), add="+")

    def _create_section_card(self, parent: tk.Misc, title: str) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=PHOENIX_THEME.card_bg,
            highlightbackground=PHOENIX_THEME.border,
            highlightthickness=1,
        )
        card.grid_columnconfigure(1, weight=1)
        tk.Label(
            card,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(PHOENIX_THEME.card_pad_y, PHOENIX_THEME.space_sm),
        )
        return card

    def _create_metric_row(self, parent: tk.Frame, title: str, row: int) -> tk.Label:
        tk.Label(
            parent,
            text=title,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_small,
            anchor="w",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            padx=(PHOENIX_THEME.card_pad_x, PHOENIX_THEME.space_md),
            pady=PHOENIX_THEME.space_xs,
        )
        value = tk.Label(
            parent,
            text="",
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_body,
            anchor="e",
            justify="right",
        )
        value.grid(
            row=row,
            column=1,
            sticky="e",
            padx=(PHOENIX_THEME.space_md, PHOENIX_THEME.card_pad_x),
            pady=PHOENIX_THEME.space_xs,
        )
        return value

    def _navigate(self, target: str) -> None:
        if self._on_navigate is not None:
            self._on_navigate(target)

    def refresh(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_refresh_at < self.REFRESH_INTERVAL_SECONDS:
            return
        self._last_refresh_at = now
        snapshot = self._read_snapshot()
        self._render(snapshot)

    def _read_snapshot(self) -> HomeSnapshot:
        try:
            self._model_controller.refresh_repository()
            models = self._model_controller.get_all_models()
            active_model_id = self._model_controller.get_active_model_id()
            installed_models = [model for model in models if model.get("installed") is True]
            active_model = next(
                (
                    str(model.get("display_name") or active_model_id)
                    for model in models
                    if model.get("id") == active_model_id
                ),
                str(active_model_id) if active_model_id else "Kein aktives Modell",
            )
        except Exception:
            installed_models = []
            active_model = "Nicht verfügbar"

        try:
            discovery = self._model_controller.get_discovery_result()
            npu_status = (
                "Verfügbar"
                if discovery.qnn_sdk_found and discovery.qnn_tools_found
                else "Nicht verfügbar"
            )
            qnn_runtime = "Gefunden" if discovery.qnn_sdk_found else "Nicht gefunden"
            onnx_runtime = (
                f"Installiert ({discovery.onnx_version})"
                if discovery.onnx_available
                else "Nicht installiert"
            )
        except Exception:
            npu_status = "Nicht verfügbar"
            qnn_runtime = "Nicht verfügbar"
            onnx_runtime = "Nicht verfügbar"

        try:
            packages = self._model_controller.reconcile_installed_packages()
            installed_package_count = sum(package.get("installed") is True for package in packages)
            installed_packages = str(installed_package_count)
        except Exception:
            installed_packages = "Nicht verfügbar"

        return HomeSnapshot(
            npu_status=npu_status,
            qnn_runtime=qnn_runtime,
            onnx_runtime=onnx_runtime,
            installed_models=str(len(installed_models)),
            active_model=active_model,
            version=BrandManager.APP_VERSION,
            branch=self._project_branch,
            installed_packages=installed_packages,
            latest_generation=self._read_latest_generation(),
        )

    def _read_project_branch(self) -> str:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=BASE,
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
                creationflags=creation_flags,
            )
            branch = result.stdout.strip()
            if branch:
                return branch
        except (OSError, subprocess.SubprocessError):
            pass
        return "Nicht verfügbar"

    def _read_latest_generation(self) -> LatestGeneration | None:
        candidates = [
            path
            for path in OUTPUT_DIR.glob("*.png")
            if path.is_file() and path.with_suffix(".json").is_file()
        ]
        if not candidates:
            return None

        latest_path = max(candidates, key=lambda path: path.stat().st_mtime_ns)
        sidecar_path = latest_path.with_suffix(".json")
        try:
            metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            metadata = {}

        model = str(metadata.get("model_id") or metadata.get("model") or "Nicht verfügbar")
        width = metadata.get("width")
        height = metadata.get("height")
        resolution = f"{width} × {height}" if width and height else "Nicht verfügbar"
        created_at = str(metadata.get("created_at") or "").strip()
        if not created_at:
            created_at = dt.datetime.fromtimestamp(latest_path.stat().st_mtime).strftime("%d.%m.%Y %H:%M")

        return LatestGeneration(
            path=latest_path,
            filename=latest_path.name,
            model=model,
            resolution=resolution,
            created_at=created_at,
        )

    def _render(self, snapshot: HomeSnapshot) -> None:
        system_values = {
            "npu": snapshot.npu_status,
            "qnn": snapshot.qnn_runtime,
            "onnx": snapshot.onnx_runtime,
            "models": snapshot.installed_models,
            "active": snapshot.active_model,
        }
        project_values = {
            "version": snapshot.version,
            "branch": snapshot.branch,
            "packages": snapshot.installed_packages,
        }
        for key, value in system_values.items():
            self._system_values[key].configure(text=value)
        for key, value in project_values.items():
            self._project_values[key].configure(text=value)

        latest = snapshot.latest_generation
        if latest is None:
            self._last_preview.grid_remove()
            self._last_message.configure(text="Es wurde noch kein Bild generiert.")
            self._last_details.configure(text="")
            self._last_generation_path = None
            self._last_generation_photo = None
            return

        if self._last_generation_path != latest.path:
            try:
                preview_size = PHOENIX_THEME.space_xl * 4
                with Image.open(latest.path) as image:
                    image.thumbnail((preview_size, preview_size))
                    self._last_generation_photo = ImageTk.PhotoImage(image.copy())
                self._last_preview.configure(image=self._last_generation_photo)
                self._last_preview.grid()
            except OSError:
                self._last_preview.grid_remove()
                self._last_generation_photo = None
            self._last_generation_path = latest.path

        self._last_message.configure(text=latest.filename)
        self._last_details.configure(
            text=(
                f"Modell: {latest.model}\n"
                f"Auflösung: {latest.resolution}\n"
                f"Erstellt: {latest.created_at}"
            )
        )
