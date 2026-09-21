import tkinter as tk
import unittest
from types import SimpleNamespace

from app.i18n import set_language
from widgets.phoenix.controls.button import PhoenixButton
from widgets.phoenix.sidebar import PhoenixSidebar
from widgets.phoenix.theme import update_phoenix_theme
from widgets.phoenix.views.image_lab_view import PhoenixImageLabView
from widgets.phoenix.views.inpainting_view import PhoenixInpaintingView
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

    def test_hub_buttons_reach_real_screens_in_both_themes(self):
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
                hub = workspace._views[workspace.current_view]
                self.assertIsInstance(hub, PhoenixImageLabView)
                labels = [w.cget("text") for w in descendants(hub) if isinstance(w, tk.Label)]
                for title in ("AI Fotorestaurierung", "Generatives Füllen", "Retusche"):
                    self.assertIn(title, labels)
                buttons = {w.text: w for w in descendants(hub) if isinstance(w, PhoenixButton)}
                for label, target, view_type in (
                    ("Fotorestaurierung öffnen", "photo_restore", PhoenixPhotoRestoreView),
                    ("Generatives Füllen öffnen", "generative_fill", PhoenixInpaintingView),
                    ("Retusche öffnen", "generative_fill", PhoenixInpaintingView),
                ):
                    buttons[label].invoke()
                    self.assertEqual(workspace.current_view, target)
                    self.assertIsInstance(workspace._views[target], view_type)
                    self.assertEqual(workspace.sidebar._buttons["inpainting"].button_type, "nav_active")
                    workspace.sidebar._buttons["inpainting"].invoke()
                    self.assertIs(workspace._views[workspace.current_view], hub)
                workspace.destroy()

    def test_image_lab_alias_opens_hub(self):
        state = SimpleNamespace(controller=None, show_view=lambda target: None)
        PhoenixWorkspace._register_views(state)
        for route in ("image_lab", "inpainting"):
            view = state._view_factories[route](self.root)
            self.assertIsInstance(view, PhoenixImageLabView)
            view.destroy()


if __name__ == "__main__":
    unittest.main()
