"""
HK NPU STUDIO - Tests for Universal Drag-and-Drop (Sprint HK-DRAGDROP-01)
Tests Gallery, Compare, and Prompt workspace drop handling, routing, format validation, and error states.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tkinter as tk
from PIL import Image

from controllers.compare_workspace_controller import CompareWorkspaceController
from controllers.gallery_controller import GalleryController
import config
from app.settings_manager import SettingsManager
from controllers.model_repository import ModelRepository
from controllers.prompt_workspace_controller import PromptWorkspaceController
from widgets.phoenix.views.compare_view import PhoenixCompareView
from widgets.phoenix.views.gallery_view import PhoenixGalleryView
from widgets.phoenix.views.prompt_view import PhoenixPromptView
from widgets.phoenix.dnd_utils import parse_dnd_paths, SUPPORTED_IMAGE_EXTENSIONS


class MockDropEvent:
    def __init__(self, data: str):
        self.data = data


class UniversalDragAndDropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="hk_dnd_test_"))

        # Create sample images
        cls.img_path = cls.temp_dir / "sample_test.png"
        Image.new("RGB", (64, 64), color="blue").save(cls.img_path)

        cls.img2_path = cls.temp_dir / "sample_test2.jpg"
        Image.new("RGB", (64, 64), color="red").save(cls.img2_path)

        # Create a subfolder with image
        cls.subfolder = cls.temp_dir / "subfolder"
        cls.subfolder.mkdir()
        cls.img_sub = cls.subfolder / "sub_image.png"
        Image.new("RGB", (64, 64), color="green").save(cls.img_sub)

        # Create preset json
        cls.json_path = cls.temp_dir / "test_preset.json"
        preset_data = {
            "generation_settings": {
                "prompt": "Test Prompt From Dropped Preset",
                "negative_prompt": "Test Negative Prompt",
                "steps": 25,
                "cfg_scale": 6.5,
                "seed": 5555,
            }
        }
        cls.json_path.write_text(json.dumps(preset_data), encoding="utf-8")

        # Create prompt txt
        cls.txt_path = cls.temp_dir / "prompt.txt"
        cls.txt_path.write_text("Detailed portrait of a futuristic robotic falcon, neon highlights", encoding="utf-8")

        # Create unsupported file
        cls.unsupported_path = cls.temp_dir / "test_binary.bin"
        cls.unsupported_path.write_bytes(b"\x00\x01\x02\x03\x04")

        cls.dest_dir = cls.temp_dir / "gallery_output"
        cls.dest_dir.mkdir()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        self.pref_dir = tempfile.TemporaryDirectory()
        self.pref_path = Path(self.pref_dir.name) / "preferences.json"
        self._pref_patcher = patch.object(
            SettingsManager, "get_preferences_path", return_value=self.pref_path
        )
        self._pref_patcher.start()

        self._model_repo_patcher = patch.object(
            ModelRepository, "_preferences_path", self.pref_path
        )
        self._model_repo_patcher.start()

        self._config_pref_patcher = patch.object(
            config, "PREFERENCES_PATH", self.pref_path
        )
        self._config_pref_patcher.start()

        self.showerror_patcher = patch("tkinter.messagebox.showerror")
        self.mock_showerror = self.showerror_patcher.start()

    def tearDown(self):
        try:
            self.root.update_idletasks()
            self.showerror_patcher.stop()
        finally:
            if hasattr(self, "_config_pref_patcher"):
                self._config_pref_patcher.stop()
            if hasattr(self, "_model_repo_patcher"):
                self._model_repo_patcher.stop()
            if hasattr(self, "_pref_patcher"):
                self._pref_patcher.stop()
            if hasattr(self, "pref_dir"):
                self.pref_dir.cleanup()

    def test_dnd_utils_path_parsing(self):
        # 1. Single path
        res = parse_dnd_paths(r"C:\test\image.png")
        self.assertEqual(res, [r"C:\test\image.png"])

        # 2. Braced paths with spaces
        res = parse_dnd_paths(r"{C:\Images\My Photo.png} {C:\Images\Other Photo.jpg}")
        self.assertEqual(res, [r"C:\Images\My Photo.png", r"C:\Images\Other Photo.jpg"])

        # 3. Space separated unix style
        res = parse_dnd_paths("C:/img1.png C:/img2.png")
        self.assertEqual(res, ["C:/img1.png", "C:/img2.png"])

        # 4. Double-quoted paths with spaces (Regression Test)
        res = parse_dnd_paths(
            r'"C:\Users\Example Folder\one.png" "C:\Users\Example Folder\two.png"'
        )
        self.assertEqual(
            res,
            [r"C:\Users\Example Folder\one.png", r"C:\Users\Example Folder\two.png"],
        )

        # 5. Mixed braced, double-quoted, single-quoted and plain paths
        res = parse_dnd_paths(
            r'{C:\Folder A\one.png} "C:\Folder B\two.png" ' + "'" + r"C:\Folder C\three.png" + "'" + r" C:\FolderD\four.png"
        )
        self.assertEqual(
            res,
            [
                r"C:\Folder A\one.png",
                r"C:\Folder B\two.png",
                r"C:\Folder C\three.png",
                r"C:\FolderD\four.png",
            ],
        )

        # 6. Preserving Windows backslashes
        raw_backslashes = r"C:\Users\User\Pictures\sub_dir\photo_01.png"
        self.assertEqual(parse_dnd_paths(f'"{raw_backslashes}"'), [raw_backslashes])

        # 7. Empty and invalid inputs
        self.assertEqual(parse_dnd_paths(""), [])
        self.assertEqual(parse_dnd_paths(None), [])
        self.assertEqual(parse_dnd_paths("   "), [])
        self.assertEqual(parse_dnd_paths('"" {}'), [])

    def test_gallery_drop_single_image(self):
        controller = GalleryController(auto_refresh=False)
        controller.current_folder = self.dest_dir
        view = PhoenixGalleryView(self.root, controller=controller)
        view._start_async_refresh = MagicMock()

        event = MockDropEvent(str(self.img_path))
        view._on_drop(event)

        expected_copied = self.dest_dir / self.img_path.name
        self.assertTrue(expected_copied.exists(), "Image was not copied to gallery destination directory")
        self.assertTrue(view._start_async_refresh.called)
        view.destroy()

    def test_gallery_drop_folder_import(self):
        controller = GalleryController(auto_refresh=False)
        controller.current_folder = self.dest_dir
        view = PhoenixGalleryView(self.root, controller=controller)
        view._start_async_refresh = MagicMock()

        event = MockDropEvent(str(self.subfolder))
        view._on_drop(event)

        expected_copied = self.dest_dir / self.img_sub.name
        self.assertTrue(expected_copied.exists(), "Image from dropped folder was not imported")
        self.assertTrue(view._start_async_refresh.called)
        view.destroy()

    def test_gallery_drop_unsupported_file(self):
        controller = GalleryController(auto_refresh=False)
        controller.current_folder = self.dest_dir
        view = PhoenixGalleryView(self.root, controller=controller)
        view._start_async_refresh = MagicMock()

        event = MockDropEvent(str(self.unsupported_path))
        view._on_drop(event)

        self.assertTrue(self.mock_showerror.called, "Error dialog was not shown for unsupported file")
        self.assertFalse(view._start_async_refresh.called)
        view.destroy()

    def test_compare_drop_panels(self):
        controller = CompareWorkspaceController()
        view = PhoenixCompareView(self.root, controller=controller)

        # 1. Drop on original panel
        view._on_panel_drop("original", [str(self.img_path)])
        state = controller.get_state()
        self.assertTrue(state.original_loaded)
        self.assertIsNotNone(state.original_metadata)
        self.assertEqual(state.original_metadata.filename, self.img_path.name)

        # 2. Drop on output panel
        view._on_panel_drop("output", [str(self.img2_path)])
        state = controller.get_state()
        self.assertTrue(state.output_loaded)
        self.assertIsNotNone(state.output_metadata)
        self.assertEqual(state.output_metadata.filename, self.img2_path.name)

        # 3. Drop 2 images onto general compare view
        controller.clear_original()
        controller.clear_output()
        event = MockDropEvent(f'"{self.img_path}" "{self.img2_path}"')
        view._on_general_drop(event)
        state = controller.get_state()
        self.assertTrue(state.original_loaded)
        self.assertTrue(state.output_loaded)
        self.assertEqual(state.original_metadata.filename, self.img_path.name)
        self.assertEqual(state.output_metadata.filename, self.img2_path.name)
        view.destroy()

    def test_compare_drop_invalid_file(self):
        controller = CompareWorkspaceController()
        view = PhoenixCompareView(self.root, controller=controller)

        res = view.load_original_from_path(self.unsupported_path)
        self.assertFalse(res)
        self.assertTrue(self.mock_showerror.called)
        view.destroy()

    def test_prompt_drop_reference_image(self):
        controller = PromptWorkspaceController()
        view = PhoenixPromptView(self.root, controller=controller)
        try:
            event = MockDropEvent(str(self.img_path))
            view._on_file_drop(event)

            self.assertEqual(view._ref_image_path, str(self.img_path))
            if getattr(view, "canny_supported", False):
                self.assertTrue(view.controlnet_canny_var.get())
        finally:
            view.destroy()

    def test_prompt_drop_preset_json(self):
        controller = PromptWorkspaceController()
        view = PhoenixPromptView(self.root, controller=controller)
        try:
            event = MockDropEvent(str(self.json_path))
            view._on_file_drop(event)

            prompt_val = view.prompt_text.get("1.0", "end-1c").strip()
            self.assertEqual(prompt_val, "Test Prompt From Dropped Preset")
            self.assertEqual(view.steps_var.get(), 25)
            self.assertAlmostEqual(view.cfg_var.get(), 6.5, places=3)
            self.assertEqual(view.seed_var.get(), "5555")
        finally:
            view.destroy()

    def test_prompt_drop_text_file(self):
        controller = PromptWorkspaceController()
        view = PhoenixPromptView(self.root, controller=controller)
        try:
            event = MockDropEvent(str(self.txt_path))
            view._on_file_drop(event)

            prompt_val = view.prompt_text.get("1.0", "end-1c").strip()
            self.assertIn("futuristic robotic falcon", prompt_val)
        finally:
            view.destroy()

    def test_prompt_drop_unsupported_file(self):
        controller = PromptWorkspaceController()
        view = PhoenixPromptView(self.root, controller=controller)
        try:
            event = MockDropEvent(str(self.unsupported_path))
            view._on_file_drop(event)
            self.assertTrue(self.mock_showerror.called)
        finally:
            view.destroy()


    def test_photo_restore_drop_valid_image(self):
        from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView
        view = PhoenixPhotoRestoreView(self.root)
        try:
            event = MockDropEvent(str(self.img_path))
            view._on_file_drop(event)
            self.assertEqual(view.input_path, self.img_path.resolve())
            self.assertIn(self.img_path.name, view.status_label.cget("text"))
        finally:
            view.destroy()

    def test_photo_restore_drop_unsupported_file(self):
        from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView
        view = PhoenixPhotoRestoreView(self.root)
        try:
            event = MockDropEvent(str(self.unsupported_path))
            view._on_file_drop(event)
            self.assertTrue(self.mock_showerror.called)
        finally:
            view.destroy()

    def test_sidebar_photo_restore_drop_opens_restoration_workflow(self):
        from widgets.phoenix.sidebar import PhoenixSidebar
        from widgets.phoenix.workspace import PhoenixWorkspace
        workspace = PhoenixWorkspace.__new__(PhoenixWorkspace)
        tk.Frame.__init__(workspace, self.root)
        workspace.controller = None
        workspace._views = {}
        workspace.current_view = "home"
        workspace.right_panel = None
        workspace.content_host = tk.Frame(workspace)
        workspace.header = MagicMock()
        workspace.open_photo_restore_with_image = MagicMock()
        sidebar = PhoenixSidebar(workspace, on_navigate=workspace.show_view)
        try:
            restore_btn = sidebar._buttons.get("inpainting")
            self.assertIsNotNone(restore_btn)
            event = MockDropEvent(str(self.img_path))
            # Test drop callback on sidebar
            sidebar._on_restore_button_drop(event)
            workspace.open_photo_restore_with_image.assert_called_once_with(str(self.img_path))
        finally:
            sidebar.destroy()
            workspace.destroy()

    def test_gui_on_drop_file_on_home_view_does_not_navigate_to_image(self):
        import gui_v2
        app = MagicMock()
        app._log = MagicMock()
        ws = MagicMock()
        ws.current_view = "home"
        ws._views = {}
        app.phoenix_workspace = ws
        app.load_image_files = MagicMock()

        event = MockDropEvent(str(self.img_path))
        gui_v2.SnapdragonAIStudioV2.on_drop_file(app, event)

        # Must not load image files or navigate to image
        app.load_image_files.assert_not_called()
        ws.show_view.assert_not_called()
        ws.show_image.assert_not_called()

    def test_gui_on_drop_file_in_photo_restore_routes_to_restore_view(self):
        import gui_v2
        app = MagicMock()
        app._log = MagicMock()
        ws = MagicMock()
        ws.current_view = "inpainting"
        restore_view = MagicMock()
        ws._views = {"inpainting": restore_view}
        app.phoenix_workspace = ws
        app.load_image_files = MagicMock()

        event = MockDropEvent(str(self.img_path))
        gui_v2.SnapdragonAIStudioV2.on_drop_file(app, event)

        restore_view._on_file_drop.assert_called_once_with(event)
        app.load_image_files.assert_not_called()


if __name__ == "__main__":
    unittest.main()
