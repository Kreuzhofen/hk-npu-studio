from __future__ import annotations

import tkinter as tk
import unittest
from types import SimpleNamespace

from app.i18n import set_language
from widgets.phoenix.sidebar import PhoenixSidebar
from widgets.phoenix.theme import update_phoenix_theme
from widgets.phoenix.views.image_lab_view import PhoenixImageLabView
from widgets.phoenix.views.image_lab_workspace import PhoenixImageLabWorkspace
from widgets.phoenix.views.image_to_image_view import PhoenixImageToImageView
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
        try:
            self.root.destroy()
        except Exception:
            pass
        update_phoenix_theme("dark")

    def _create_test_workspace(self) -> PhoenixWorkspace:
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
        return workspace

    def test_global_sidebar_has_image_lab_main_button(self):
        workspace = self._create_test_workspace()
        try:
            # Phoenix Image Lab must remain an independent main button
            self.assertIn("inpainting", workspace.sidebar._buttons)
            btn = workspace.sidebar._buttons["inpainting"]
            self.assertEqual(btn.cget("text"), "Phoenix Image Lab")
            # Individual sub-apps must NOT be standalone buttons in global sidebar
            self.assertNotIn("photo_restore", workspace.sidebar._buttons)
            self.assertNotIn("generative_fill", workspace.sidebar._buttons)
            self.assertNotIn("retouch", workspace.sidebar._buttons)
        finally:
            workspace.destroy()

    def test_image_lab_has_no_secondary_sidebar_and_opens_overview_in_both_themes(self):
        for theme in ("dark", "light"):
            with self.subTest(theme=theme):
                update_phoenix_theme(theme)
                workspace = self._create_test_workspace()
                try:
                    workspace.sidebar._buttons["inpainting"].invoke()
                    lab_ws = workspace._views[workspace.current_view]

                    self.assertEqual(workspace.current_view, "inpainting")
                    self.assertIsInstance(lab_ws, PhoenixImageLabWorkspace)
                    self.assertEqual(workspace.sidebar._buttons["inpainting"].button_type, "nav_active")

                    # Verify local vertical navigation sidebar is completely removed
                    self.assertFalse(hasattr(lab_ws, "local_sidebar"))
                    self.assertFalse(hasattr(lab_ws, "divider"))
                    self.assertFalse(hasattr(lab_ws, "nav_header"))

                    # Default subview is overview
                    self.assertEqual(lab_ws.active_subview, "overview")

                    # Verify overview card content is active and full width
                    subview = lab_ws._subviews["overview"]
                    self.assertIsInstance(subview, PhoenixImageLabView)
                finally:
                    workspace.destroy()

    def test_overview_cards_trigger_all_subviews_and_back_navigation(self):
        workspace = self._create_test_workspace()
        try:
            workspace.show_view("inpainting")
            lab_ws: PhoenixImageLabWorkspace = workspace._views["inpainting"]
            overview: PhoenixImageLabView = lab_ws._subviews["overview"]

            # 1. Trigger Generatives Füllen via Overview Card
            overview._navigate("generative_fill")
            self.assertEqual(lab_ws.active_subview, "generative_fill")
            fill_view = lab_ws._subviews["generative_fill"]
            self.assertIsInstance(fill_view, PhoenixInpaintingView)

            # Return to Overview via toolbar button
            fill_view.overview_button.invoke()
            self.assertEqual(lab_ws.active_subview, "overview")

            # 2. Trigger Retusche via Overview Card
            overview._navigate("retouch")
            self.assertEqual(lab_ws.active_subview, "retouch")
            retouch_view = lab_ws._subviews["retouch"]
            self.assertIsInstance(retouch_view, PhoenixInpaintingView)
            self.assertIs(retouch_view, fill_view)

            # Return to Overview via toolbar button
            retouch_view.overview_button.invoke()
            self.assertEqual(lab_ws.active_subview, "overview")

            # 3. Trigger Foto-Restaurierung via Overview Card
            overview._navigate("photo_restore")
            self.assertEqual(lab_ws.active_subview, "photo_restore")
            restore_view = lab_ws._subviews["photo_restore"]
            self.assertIsInstance(restore_view, PhoenixPhotoRestoreView)

            # Return to Overview via toolbar button
            restore_view.overview_button.invoke()
            self.assertEqual(lab_ws.active_subview, "overview")

            # 4. Trigger Image-to-Image via Overview Card
            overview._navigate("image_to_image")
            self.assertEqual(lab_ws.active_subview, "image_to_image")
            i2i_view = lab_ws._subviews["image_to_image"]
            self.assertIsInstance(i2i_view, PhoenixImageToImageView)

            # Return to Overview via toolbar button
            i2i_view.overview_button.invoke()
            self.assertEqual(lab_ws.active_subview, "overview")
        finally:
            workspace.destroy()

    def test_image_to_image_drag_and_drop_delegation(self):
        workspace = self._create_test_workspace()
        try:
            workspace.show_view("inpainting")
            lab_ws: PhoenixImageLabWorkspace = workspace._views["inpainting"]
            lab_ws.select_subview("overview")
            self.assertEqual(lab_ws.active_subview, "overview")

            i2i_view = lab_ws._get_or_create_subview("image_to_image")
            called_with = []
            i2i_view.load_dropped_image = lambda path: called_with.append(path)

            workspace.open_image_to_image_with_image("test_sample.png")
            self.assertEqual(lab_ws.active_subview, "image_to_image")
            self.assertEqual(called_with, ["test_sample.png"])
        finally:
            workspace.destroy()

    def test_photo_restore_drag_and_drop_delegation(self):
        workspace = self._create_test_workspace()
        try:
            workspace.show_view("inpainting")
            lab_ws: PhoenixImageLabWorkspace = workspace._views["inpainting"]

            lab_ws.select_subview("overview")
            self.assertEqual(lab_ws.active_subview, "overview")

            restore_view = lab_ws._get_or_create_subview("photo_restore")
            called_with = []
            restore_view.load_dropped_image = lambda path: called_with.append(path)

            workspace.open_photo_restore_with_image("test_sample.png")
            self.assertEqual(lab_ws.active_subview, "photo_restore")
            self.assertEqual(called_with, ["test_sample.png"])
        finally:
            workspace.destroy()

    def test_overview_button_configuration_and_theme_parity(self):
        for theme in ("dark", "light"):
            with self.subTest(theme=theme):
                update_phoenix_theme(theme)

                # Test PhoenixInpaintingView toolbar button
                inpainting = PhoenixInpaintingView(self.root)
                try:
                    self.assertTrue(hasattr(inpainting, "overview_button"))
                    btn = inpainting.overview_button
                    self.assertEqual(btn.cget("text"), "Übersicht")
                    self.assertEqual(btn.button_type, "neutral")
                    self.assertEqual(btn.icon_name, "back")
                    self.assertEqual(btn.radius, 6)
                    self.assertEqual(btn._height, 32)
                    self.assertIs(inpainting._toolbar_items[0], btn)
                finally:
                    inpainting.destroy()

                # Test PhoenixPhotoRestoreView toolbar button
                restore = PhoenixPhotoRestoreView(self.root)
                try:
                    self.assertTrue(hasattr(restore, "overview_button"))
                    btn = restore.overview_button
                    self.assertEqual(btn.cget("text"), "Übersicht")
                    self.assertEqual(btn.button_type, "neutral")
                    self.assertEqual(btn.icon_name, "back")
                    self.assertEqual(btn.radius, 6)
                    self.assertEqual(btn._height, 32)
                finally:
                    restore.destroy()

                # Test PhoenixImageToImageView toolbar button
                i2i = PhoenixImageToImageView(self.root)
                try:
                    self.assertTrue(hasattr(i2i, "overview_button"))
                    btn = i2i.overview_button
                    self.assertEqual(btn.cget("text"), "Übersicht")
                    self.assertEqual(btn.button_type, "neutral")
                    self.assertEqual(btn.icon_name, "back")
                    self.assertEqual(btn.radius, 6)
                    self.assertEqual(btn._height, 32)
                finally:
                    i2i.destroy()

    def test_overview_button_navigation_and_state_preservation(self):
        workspace = self._create_test_workspace()
        try:
            workspace.show_view("inpainting")
            lab_ws: PhoenixImageLabWorkspace = workspace._views["inpainting"]

            # 1. Switch to Generatives Füllen
            lab_ws.select_subview("generative_fill")
            fill_view: PhoenixInpaintingView = lab_ws._subviews["generative_fill"]

            # Set user state in inpainting view
            fill_view.prompt.delete("1.0", "end")
            fill_view.prompt.insert("1.0", "A golden retriever in a field")
            fill_view.negative_prompt.delete("1.0", "end")
            fill_view.negative_prompt.insert("1.0", "blurry, low quality")
            fill_view.steps.set(28)
            fill_view.cfg_var.set(8.5)

            # Click toolbar overview button
            fill_view.overview_button.invoke()
            self.assertEqual(lab_ws.active_subview, "overview")

            # Navigate back to Generatives Füllen
            lab_ws.select_subview("generative_fill")
            self.assertEqual(lab_ws.active_subview, "generative_fill")
            self.assertIs(lab_ws._subviews["generative_fill"], fill_view)
            self.assertEqual(fill_view.prompt.get("1.0", "end-1c"), "A golden retriever in a field")
            self.assertEqual(fill_view.negative_prompt.get("1.0", "end-1c"), "blurry, low quality")
            self.assertEqual(fill_view.steps.get(), 28)

            # 2. Switch to Photo Restore
            lab_ws.select_subview("photo_restore")
            restore_view = lab_ws._subviews["photo_restore"]
            restore_view.overview_button.invoke()
            self.assertEqual(lab_ws.active_subview, "overview")
            lab_ws.select_subview("photo_restore")
            self.assertEqual(lab_ws.active_subview, "photo_restore")
        finally:
            workspace.destroy()


if __name__ == "__main__":
    unittest.main()
