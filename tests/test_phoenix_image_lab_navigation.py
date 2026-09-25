import tkinter as tk
import unittest
from types import SimpleNamespace

from app.i18n import set_language
from widgets.phoenix.sidebar import PhoenixSidebar
from widgets.phoenix.theme import update_phoenix_theme
from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView
from widgets.phoenix.workspace import PhoenixWorkspace


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class ImageLabNavigationTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        set_language("de_DE")

    def tearDown(self):
        self.root.destroy()
        update_phoenix_theme("dark")

    def test_image_lab_opens_photo_restore_directly_in_both_themes(self):
        for theme in ("dark", "light"):
            with self.subTest(theme=theme):
                update_phoenix_theme(theme)
                workspace = PhoenixWorkspace.__new__(PhoenixWorkspace)
                tk.Frame.__init__(workspace, self.root)
                workspace.controller = None
                workspace._views = {}
                workspace.current_view = None
                workspace.right_panel = None
                workspace.content_host = tk.Frame(workspace)
                workspace.header = SimpleNamespace(set_view=lambda title: None)
                workspace.sidebar = PhoenixSidebar(workspace, on_navigate=workspace.show_view)
                workspace._register_views()
                self.assertNotIn("photo_restore", workspace.sidebar._buttons)
                workspace.sidebar._buttons["inpainting"].invoke()
                restore = workspace._views[workspace.current_view]
                self.assertEqual(workspace.current_view, "inpainting")
                self.assertIsInstance(restore, PhoenixPhotoRestoreView)
                self.assertEqual(workspace.sidebar._buttons["inpainting"].button_type, "nav_active")
                visible_text = [
                    str(widget.cget("text"))
                    for widget in descendants(restore)
                    if isinstance(widget, (tk.Label, tk.Button))
                ]
                joined = "\n".join(visible_text)
                self.assertIn(
                    "Historische und Schwarz-Weiß-Fotos restaurieren, Details bewahren und hochskalieren – lokal auf der Snapdragon® NPU.",
                    joined,
                )
                for excluded in (
                    "Generatives Füllen",
                    "Retusche öffnen",
                    "Object Removal",
                    "Farbrekonstruktion",
                ):
                    self.assertNotIn(excluded, joined)
                self.assertNotIn("generative_fill", workspace._views)
                workspace._view_factories["home"] = tk.Frame
                workspace.sidebar._buttons["home"].invoke()
                self.assertEqual(workspace.current_view, "home")
                workspace.sidebar._buttons["inpainting"].invoke()
                self.assertEqual(workspace.current_view, "inpainting")
                self.assertIs(workspace._views["inpainting"], restore)
                workspace.destroy()

    def test_image_lab_aliases_open_photo_restore(self):
        state = SimpleNamespace(controller=None, show_view=lambda target: None)
        PhoenixWorkspace._register_views(state)
        for route in ("image_lab", "inpainting"):
            view = state._view_factories[route](self.root)
            self.assertIsInstance(view, PhoenixPhotoRestoreView)
            view.destroy()


if __name__ == "__main__":
    unittest.main()
