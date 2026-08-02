from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import json
from pathlib import Path
import subprocess
import time
import tkinter as tk
from tkinter import messagebox
import shutil
from typing import Callable

from PIL import Image, ImageTk

from config import BASE, OUTPUT_DIR
from controllers.model_manager_controller import ModelManagerController
from engine.brand_manager import BrandManager
from widgets.phoenix.theme import PHOENIX_THEME
from app.i18n import tr
from app.settings_manager import SettingsManager


@dataclass(frozen=True)
class GenerationInfo:
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
    disk_usage_info: str
    latest_generations: list[GenerationInfo]


class PhoenixHomeView(tk.Frame):
    """Real-data control center for the Phoenix workspace."""

    REFRESH_INTERVAL_SECONDS = 5.0

    @staticmethod
    def _execution_provider_status(discovery: object) -> str:
        configured_provider = SettingsManager.get_execution_provider()
        if configured_provider == SettingsManager.CPU_EXECUTION_PROVIDER:
            return SettingsManager.CPU_EXECUTION_PROVIDER
        if (
            getattr(discovery, "qnn_sdk_found", False)
            and getattr(discovery, "qnn_tools_found", False)
        ):
            return SettingsManager.QNN_EXECUTION_PROVIDER
        return tr("home_qnn_not_registered", "QNN nicht registriert")

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
        self._cached_photos: list[ImageTk.PhotoImage] = []

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
            pady=(PHOENIX_THEME.space_md, PHOENIX_THEME.space_sm),
        )
        tk.Label(
            welcome,
            text=tr("home_welcome", "Willkommen"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_muted,
            font=PHOENIX_THEME.font_card_title,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            welcome,
            text=tr("app_title", "Snapdragon AI Studio"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_title,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))
        tk.Label(
            welcome,
            text=tr("app_tagline", "Create. Organize. Review. Evolve."),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_secondary,
            font=PHOENIX_THEME.font_body,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        actions = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        actions.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_sm),
        )
        tk.Label(
            actions,
            text=tr("home_quickstart", "Schnelleinstieg"),
            bg=PHOENIX_THEME.content_bg,
            fg=PHOENIX_THEME.text_primary,
            font=PHOENIX_THEME.font_section,
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        
        for column in range(3):
            actions.grid_columnconfigure(column, weight=1, uniform="home_actions")

        action_specs = (
            ("🎨", tr("home_action_generate", "Neue Bildgenerierung"), "prompt"),
            ("🤖", tr("home_action_models", "Modelle verwalten"), "models"),
            ("📚", tr("home_action_gallery", "Galerie"), "gallery"),
        )
        for column, (icon, title, target) in enumerate(action_specs):
            self._create_action_card(actions, icon, title, target, column)

        status_host = tk.Frame(self, bg=PHOENIX_THEME.content_bg)
        status_host.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_sm),
        )
        status_host.grid_columnconfigure((0, 1), weight=1, uniform="home_status")

        system_card = self._create_section_card(status_host, tr("home_sys_npu_status", "System- & NPU-Status"))
        system_card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, PHOENIX_THEME.space_sm),
        )
        
        self._system_values["npu"] = self._create_metric_row(system_card, tr("home_hexagon_npu", "Qualcomm Hexagon NPU"), 1)
        self._system_values["active"] = self._create_metric_row(system_card, tr("home_active_model_lbl", "Aktives Modell"), 2)
        self._system_values["resources"] = self._create_metric_row(system_card, tr("home_sys_resources", "Systemressourcen"), 3)

        project_card = self._create_section_card(status_host, tr("home_project_status", "Projektstatus"))
        project_card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(PHOENIX_THEME.space_sm, 0),
        )
        
        self._project_values["version"] = self._create_metric_row(project_card, tr("home_version", "Version"), 1)
        self._project_values["branch"] = self._create_metric_row(project_card, tr("home_branch", "Branch"), 2)
        self._project_values["packages"] = self._create_metric_row(project_card, tr("home_installed_packages", "Installierte AI Packages"), 3)

        self._last_card = self._create_section_card(self, tr("home_latest_generations", "Letzte Generierungen"))
        self._last_card.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=PHOENIX_THEME.space_xl,
            pady=(0, PHOENIX_THEME.space_md),
        )
        self._last_card.grid_columnconfigure(0, weight=1)
        self._delete_all_btn = tk.Button(
            self._last_card,
            text=tr("home_delete_all", "Alle löschen"),
            command=self._delete_all_generations,
            bg=PHOENIX_THEME.elevated_bg,
            fg=PHOENIX_THEME.danger,
            activebackground=PHOENIX_THEME.danger,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            padx=PHOENIX_THEME.button_pad_x,
            pady=PHOENIX_THEME.space_xs,
            font=PHOENIX_THEME.font_button,
            cursor="hand2",
        )
        self._delete_all_btn.grid(
            row=0,
            column=1,
            sticky="e",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(8, 4),
        )
        
        self._previews_inner_frame = tk.Frame(self._last_card, bg=PHOENIX_THEME.card_bg)
        self._previews_inner_frame.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(4, PHOENIX_THEME.card_pad_y)
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
                0 if column == 2 else PHOENIX_THEME.space_sm,
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
        icon_label.pack(anchor="w", padx=PHOENIX_THEME.card_pad_x, pady=(8, 0))
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
            pady=(4, 8),
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
            columnspan=1,
            sticky="ew",
            padx=PHOENIX_THEME.card_pad_x,
            pady=(8, 4),
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
            pady=2,
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
            pady=2,
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
                str(active_model_id) if active_model_id else tr("home_no_active_model", "Kein aktives Modell"),
            )
        except Exception:
            installed_models = []
            active_model = tr("home_not_available", "Nicht verfügbar")

        try:
            discovery = self._model_controller.get_discovery_result()
            npu_status = self._execution_provider_status(discovery)
            qnn_runtime = tr("home_found", "Gefunden") if discovery.qnn_sdk_found else tr("home_not_found", "Nicht gefunden")
            onnx_runtime = (
                f"{tr('home_installed_label', 'Installiert')} ({discovery.onnx_version})"
                if discovery.onnx_available
                else tr("home_not_installed", "Nicht installiert")
            )
        except Exception:
            npu_status = tr("home_not_available", "Nicht verfügbar")
            qnn_runtime = tr("home_not_available", "Nicht verfügbar")
            onnx_runtime = tr("home_not_available", "Nicht verfügbar")

        try:
            packages = self._model_controller.reconcile_installed_packages()
            installed_package_count = sum(package.get("installed") is True for package in packages)
            installed_packages = str(installed_package_count)
        except Exception:
            installed_packages = tr("home_not_available", "Nicht verfügbar")

        try:
            usage = shutil.disk_usage(BASE)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            disk_usage_info = tr("home_disk_free", "{free:.1f} GB frei (von {total:.1f} GB)").format(free=free_gb, total=total_gb)
        except Exception:
            disk_usage_info = tr("home_not_available", "Nicht verfügbar")

        return HomeSnapshot(
            npu_status=npu_status,
            qnn_runtime=qnn_runtime,
            onnx_runtime=onnx_runtime,
            installed_models=str(len(installed_models)),
            active_model=active_model,
            version=BrandManager.APP_VERSION,
            branch=self._project_branch,
            installed_packages=installed_packages,
            disk_usage_info=disk_usage_info,
            latest_generations=self._read_latest_generations(),
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
        return tr("home_not_available", "Nicht verfügbar")

    def _read_latest_generations(self) -> list[GenerationInfo]:
        candidates = [
            path
            for path in OUTPUT_DIR.glob("*.png")
            if path.is_file()
        ]
        if not candidates:
            return []

        # Sort by modification time, newest first
        candidates.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
        latest_candidates = candidates[:4]

        info_list = []
        for path in latest_candidates:
            sidecar_path = path.with_suffix(".json")
            try:
                metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                metadata = {}

            model = str(metadata.get("model_id") or metadata.get("model") or tr("home_not_available", "Nicht verfügbar"))
            width = metadata.get("width")
            height = metadata.get("height")
            resolution = f"{width} × {height}" if width and height else tr("home_not_available", "Nicht verfügbar")
            created_at = str(metadata.get("created_at") or "").strip()
            if not created_at:
                created_at = dt.datetime.fromtimestamp(path.stat().st_mtime).strftime("%d.%m.%Y %H:%M")

            info_list.append(
                GenerationInfo(
                    path=path,
                    filename=path.name,
                    model=model,
                    resolution=resolution,
                    created_at=created_at,
                )
            )
        return info_list

    def _truncate_text(self, text: str, max_length: int = 15) -> str:
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def _render(self, snapshot: HomeSnapshot) -> None:
        system_values = {
            "npu": snapshot.npu_status,
            "active": snapshot.active_model,
            "resources": snapshot.disk_usage_info,
        }
        project_values = {
            "version": snapshot.version,
            "branch": snapshot.branch,
            "packages": snapshot.installed_packages,
        }
        for key, value in system_values.items():
            if key in self._system_values:
                self._system_values[key].configure(text=value)
        for key, value in project_values.items():
            if key in self._project_values:
                self._project_values[key].configure(text=value)

        # Clear existing preview tiles inside self._previews_inner_frame
        for widget in self._previews_inner_frame.winfo_children():
            widget.destroy()

        latest = snapshot.latest_generations
        if not latest:
            self._delete_all_btn.configure(state="disabled", fg=PHOENIX_THEME.text_disabled, cursor="arrow")
            no_gen_lbl = tk.Label(
                self._previews_inner_frame,
                text=tr("home_no_images_generated", "Es wurden noch keine Bilder generiert."),
                bg=PHOENIX_THEME.card_bg,
                fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_body,
            )
            no_gen_lbl.pack(pady=12)
            self._cached_photos.clear()
            return

        self._delete_all_btn.configure(state="normal", fg=PHOENIX_THEME.danger, cursor="hand2")
        self._cached_photos.clear()

        # Configure columns inside previews frame for horizontal distribution
        for idx in range(4):
            self._previews_inner_frame.grid_columnconfigure(idx, weight=1, uniform="home_previews")

        for idx, gen in enumerate(latest):
            tile_frame = tk.Frame(
                self._previews_inner_frame,
                bg=PHOENIX_THEME.elevated_bg,
                highlightbackground=PHOENIX_THEME.border,
                highlightthickness=1,
                cursor="hand2"
            )
            tile_frame.grid(row=0, column=idx, padx=4, pady=2, sticky="nsew")

            try:
                with Image.open(gen.path) as img:
                    img.thumbnail((120, 80))
                    photo = ImageTk.PhotoImage(img.copy())
                    self._cached_photos.append(photo)
            except Exception:
                photo = None

            img_lbl = tk.Label(
                tile_frame,
                image=photo if photo else "",
                bg=PHOENIX_THEME.elevated_bg,
                width=120,
                height=80,
                cursor="hand2"
            )
            img_lbl.pack(padx=4, pady=4)

            name_lbl = tk.Label(
                tile_frame,
                text=self._truncate_text(gen.filename),
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.text_secondary,
                font=PHOENIX_THEME.font_caption,
                cursor="hand2"
            )
            name_lbl.pack(padx=4, pady=(0, 4))

            delete_btn = tk.Button(
                tile_frame,
                text="×",
                command=lambda path=gen.path: self._delete_generation(path),
                bg=PHOENIX_THEME.elevated_bg,
                fg=PHOENIX_THEME.danger,
                activebackground=PHOENIX_THEME.danger,
                activeforeground=PHOENIX_THEME.text_on_accent,
                relief="flat",
                bd=0,
                font=PHOENIX_THEME.font_button,
                cursor="hand2",
                width=2,
            )
            delete_btn.place(relx=1.0, x=-4, y=4, anchor="ne")

            # Hover function closure
            def make_hover_func(f=tile_frame, il=img_lbl, nl=name_lbl, db=delete_btn):
                return lambda active: (
                    f.configure(highlightbackground=PHOENIX_THEME.accent if active else PHOENIX_THEME.border),
                    f.configure(bg=PHOENIX_THEME.card_bg if active else PHOENIX_THEME.elevated_bg),
                    il.configure(bg=PHOENIX_THEME.card_bg if active else PHOENIX_THEME.elevated_bg),
                    nl.configure(bg=PHOENIX_THEME.card_bg if active else PHOENIX_THEME.elevated_bg),
                    db.configure(bg=PHOENIX_THEME.card_bg if active else PHOENIX_THEME.elevated_bg),
                )

            hover_func = make_hover_func()
            click_func = lambda _event, target="gallery": self._navigate(target)

            for w in (tile_frame, img_lbl, name_lbl):
                w.bind("<Enter>", lambda _e, h=hover_func: h(True), add="+")
                w.bind("<Leave>", lambda _e, h=hover_func: h(False), add="+")
                w.bind("<Button-1>", click_func, add="+")
                w.bind(
                    "<Button-3>",
                    lambda event, path=gen.path: self._show_generation_menu(event, path),
                    add="+",
                )

            # Handler creators to avoid loop-closure issues in Python
            def make_btn_handlers(f=tile_frame, il=img_lbl, nl=name_lbl, db=delete_btn, h=hover_func):
                def on_enter(e):
                    h(True)
                    db.configure(bg=PHOENIX_THEME.danger, fg=PHOENIX_THEME.text_on_accent)
                def on_leave(e):
                    x = f.winfo_pointerx()
                    y = f.winfo_pointery()
                    widget = f.winfo_containing(x, y)
                    if widget in (f, il, nl):
                        h(True)
                        db.configure(bg=PHOENIX_THEME.card_bg, fg=PHOENIX_THEME.danger)
                    else:
                        h(False)
                        db.configure(bg=PHOENIX_THEME.elevated_bg, fg=PHOENIX_THEME.danger)
                return on_enter, on_leave

            btn_enter, btn_leave = make_btn_handlers()
            delete_btn.bind("<Enter>", btn_enter, add="+")
            delete_btn.bind("<Leave>", btn_leave, add="+")

    def _show_generation_menu(self, event: tk.Event, path: Path) -> None:
        menu = tk.Menu(
            self,
            tearoff=False,
            bg=PHOENIX_THEME.card_bg,
            fg=PHOENIX_THEME.text_primary,
            activebackground=PHOENIX_THEME.accent,
            activeforeground=PHOENIX_THEME.text_on_accent,
            relief="flat",
            bd=0,
            font=PHOENIX_THEME.font_body,
        )
        menu.add_command(
            label=tr("home_open_in_explorer", "Im Explorer öffnen"),
            command=lambda: self._open_in_explorer(path),
        )
        menu.add_command(
            label=tr("home_delete_generation", "Generierung löschen"),
            command=lambda: self._delete_generation(path),
        )
        menu.tk_popup(event.x_root, event.y_root)

    def _open_in_explorer(self, path: Path) -> None:
        path = path.resolve()
        if not path.exists():
            messagebox.showerror(
                tr("home_error_title", "Fehler"),
                tr("home_file_not_found", "Die Bilddatei konnte nicht gefunden werden: {path}").format(path=path),
                parent=self
            )
            return
        try:
            subprocess.run(["explorer", "/select,", str(path)])
        except Exception as e:
            messagebox.showerror(
                tr("home_error_title", "Fehler"),
                tr("home_explorer_error", "Fehler beim Öffnen des Explorers: {error}").format(error=str(e)),
                parent=self
            )

    @staticmethod
    def _generation_files(path: Path) -> tuple[Path, ...]:
        return path, path.with_suffix(".json")

    def _delete_generation(self, path: Path) -> None:
        if not messagebox.askyesno(
            tr("home_delete_generation_title", "Generierung löschen"),
            tr(
                "home_delete_generation_confirm",
                "Soll die ausgewählte Generierung einschließlich Metadaten dauerhaft gelöscht werden?",
            ),
            parent=self,
        ):
            return
        for candidate in self._generation_files(path):
            candidate.unlink(missing_ok=True)
        self.refresh(force=True)

    def _delete_all_generations(self) -> None:
        latest = self._read_latest_generations()
        if not latest:
            return
        count = len(latest)
        if not messagebox.askyesno(
            tr("home_delete_all_title", "Alle Generierungen löschen"),
            tr(
                "home_delete_all_confirm_with_count",
                "Sollen wirklich alle {count} angezeigten Generierungen einschließlich Metadaten dauerhaft gelöscht werden? Diese Aktion kann nicht rückgängig gemacht werden.",
            ).format(count=count),
            parent=self,
        ):
            return
        for gen in latest:
            for candidate in self._generation_files(gen.path):
                candidate.unlink(missing_ok=True)
        self.refresh(force=True)
