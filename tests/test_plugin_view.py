import tkinter as tk
from unittest.mock import MagicMock

from widgets.phoenix.theme import PHOENIX_THEME
from widgets.phoenix.views.plugin_view import PhoenixPluginView


def test_plugin_install_action_stays_outside_scrollable_content() -> None:
    root = tk.Tk()
    try:
        root.geometry("480x420")
        controller = MagicMock()
        controller.get_plugins.return_value = []
        view = PhoenixPluginView(root, controller=controller)
        view.pack(fill="both", expand=True)
        root.update_idletasks()

        assert view.install_btn.winfo_manager() == "grid"
        assert view.install_frame.master is view.content_slot
        assert view.middle_frame.master is view.content_slot
        assert view.canvas.master is view.middle_frame
        assert view.install_btn.command == view._on_install_plugin
        assert view.install_btn.normal_bg == PHOENIX_THEME.accent
        assert view.middle_frame.winfo_y() + view.middle_frame.winfo_height() <= view.install_frame.winfo_y()
        assert view.install_btn.winfo_y() + view.install_btn.winfo_height() <= (
            view.install_frame.winfo_y() + view.install_frame.winfo_height()
        )
        assert view.install_frame.winfo_y() + view.install_frame.winfo_height() <= view.winfo_height()
        assert view.canvas.cget("scrollregion")

        root.geometry("480x760")
        root.update_idletasks()
        root.geometry("480x420")
        root.update_idletasks()
        assert view.install_btn.winfo_manager() == "grid"
        assert view.canvas.cget("scrollregion")
    finally:
        root.destroy()
