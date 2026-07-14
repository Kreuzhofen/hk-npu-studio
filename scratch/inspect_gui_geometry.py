import sys
sys.path.append('.')
import tkinter as tk
from unittest.mock import MagicMock
from engine.theme_manager import ThemeManager, ThemePalette

# Setup a mock palette for widgets/phoenix/theme initialization
dummy_palette = ThemePalette(
    background="#ffffff",
    surface="#ffffff",
    card="#ffffff",
    elevated="#f3f2f1",
    border="#cccccc",
    accent="#0078d4",
    success="#22c55e",
    warning="#eab308",
    error="#ef4444",
    text="#000000",
    text_secondary="#333333",
    text_disabled="#999999",
    text_on_accent="#ffffff",
    button="#ffffff",
    button_hover="#ffffff",
    button_active="#005a9e",
    sidebar="#ffffff",
    header="#ffffff",
    workspace="#ffffff",
)
ThemeManager.palette = MagicMock(return_value=dummy_palette)

from controllers.prompt_workspace_controller import PromptWorkspaceController
from widgets.phoenix.views.prompt_view import PhoenixPromptView

root = tk.Tk()
controller = PromptWorkspaceController()
view = PhoenixPromptView(root, controller=controller)

root.update()

print("Preset frame is_mapped:", view.steps_preset_frame.winfo_ismapped())
print("Preset frame width/height:", view.steps_preset_frame.winfo_width(), "x", view.steps_preset_frame.winfo_height())
print("Schnell button is_mapped:", view.btn_preset_schnell.winfo_ismapped())
print("Schnell button width/height:", view.btn_preset_schnell.winfo_width(), "x", view.btn_preset_schnell.winfo_height())
print("Standard button width/height:", view.btn_preset_standard.winfo_width(), "x", view.btn_preset_standard.winfo_height())
print("Beste button width/height:", view.btn_preset_beste.winfo_width(), "x", view.btn_preset_beste.winfo_height())

root.destroy()
