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

print("Steps scale grid info:", view.steps_scale.grid_info())
print("Preset frame grid info:", view.steps_preset_frame.grid_info())
print("Buttons grid info:")
print("  Schnell:", view.btn_preset_schnell.grid_info())
print("  Standard:", view.btn_preset_standard.grid_info())
print("  Beste:", view.btn_preset_beste.grid_info())

print("Preset frame children:")
for child in view.steps_preset_frame.winfo_children():
    print("  Child:", child, "grid info:", child.grid_info())

root.destroy()
