from __future__ import annotations

import tkinter as tk

import pytest

from app.i18n import set_language
from app.runtime_localization import localize_runtime_text
from widgets.plugin_card import PluginCard
from widgets.queue_card import QueueCard
from widgets.status_bar import StatusBar


@pytest.mark.parametrize(
    ("locale", "ready", "running", "completed", "cancelled", "error_prefix"),
    (
        ("de_DE", "Bereit", "Läuft", "Fertig", "ABGEBROCHEN", "Fehler:"),
        ("en_US", "Ready", "Running", "Completed", "CANCELLED", "Error:"),
        ("es_ES", "Listo", "En ejecución", "Terminado", "CANCELADO", "Error:"),
    ),
)
def test_runtime_status_aliases_follow_selected_language(
    locale, ready, running, completed, cancelled, error_prefix
):
    try:
        set_language(locale)
        for alias in ("ready", "Bereit", "Listo"):
            assert localize_runtime_text(alias) == ready
        for alias in ("running", "Läuft", "En ejecución"):
            assert localize_runtime_text(alias) == running
        for alias in ("completed", "Abgeschlossen", "Completado"):
            assert localize_runtime_text(alias) == completed
        for alias in ("cancelled", "Abgebrochen", "Cancelado"):
            assert localize_runtime_text(alias) == cancelled
        assert localize_runtime_text("Fehler: details").startswith(error_prefix)
    finally:
        set_language("de_DE")


def test_dynamic_status_widgets_translate_canonical_values(tmp_path):
    root = tk.Tk()
    root.withdraw()
    try:
        expected = {
            "de_DE": ("Bereit", "Läuft", "Wartet"),
            "en_US": ("Ready", "Running", "Waiting"),
            "es_ES": ("Listo", "En ejecución", "En espera"),
        }
        for locale, (ready, running, waiting) in expected.items():
            set_language(locale)

            status_bar = StatusBar(root)
            status_bar.set_status(engine_status="ready", worker_status="running")
            status_text = status_bar.status_label.cget("text")
            assert ready in status_text
            assert running in status_text

            plugin_card = PluginCard(root)
            plugin_card.set_plugin("Plugin", "QNN", "running")
            assert running in plugin_card.status_label.cget("text")

            image = tmp_path / f"{locale}.png"
            image.write_bytes(b"image")
            queue = QueueCard(root, on_select=lambda _path: None)
            queue.set_jobs([{"input_path": str(image), "status": "waiting"}])
            assert waiting in queue.listbox.get(0)

            status_bar.destroy()
            plugin_card.destroy()
            queue.destroy()
    finally:
        root.destroy()
        set_language("de_DE")
