from __future__ import annotations

import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from dialogs.model_direct_download_dialog import ModelDirectDownloadDialog
from dialogs.studio_dialog import StudioDialog
from widgets.phoenix.views.model_manager_view import PhoenixModelManagerView


class ModelDownloadDialogLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def test_model_inspector_scrolls_details_with_fixed_action_frame(self) -> None:
        repository = MagicMock()
        repository.list_models = None
        repository.get_models = None
        repository.available_models = None
        repository.get_all_models.return_value = []
        repository.get_active_model_id.return_value = None
        controller = MagicMock()
        controller.model.repository = repository

        view = PhoenixModelManagerView(self.root, controller=controller)
        self.root.update_idletasks()
        self.assertIs(view.insp_content.master, view.insp_canvas)
        self.assertEqual(view.insp_canvas.grid_info()["row"], 0)
        self.assertEqual(view.action_frame.grid_info()["row"], 1)
        self.assertEqual(view.action_frame.winfo_manager(), "grid")
        view._resize_inspector_content(MagicMock(width=360))
        self.assertEqual(view.insp_canvas.itemcget(view.insp_canvas_window, "width"), "360")
        self.assertLess(int(view.det_desc.cget("wraplength")), 360)
        self.assertNotEqual(int(view.det_desc.cget("wraplength")), 300)
        view.destroy()

    def test_dialog_limits_small_work_area_and_keeps_footer_callbacks(self) -> None:
        start_install = MagicMock(return_value=True)
        with patch.object(ModelDirectDownloadDialog, "_get_work_area", return_value=(0, 0, 1366, 680)), \
             patch.object(ModelDirectDownloadDialog, "wait_window", return_value=None):
            dialog = ModelDirectDownloadDialog(
                self.root,
                model_name="Test model",
                download_size=1,
                start_install=start_install,
                on_installed=MagicMock(),
                on_open_generate=MagicMock(),
            )
        self.assertLessEqual(dialog.dialog_size[1], 632)
        self.assertLessEqual(dialog.dialog_min_size[1], 632)
        self.assertEqual(dialog.start_button.winfo_manager(), "grid")
        self.assertEqual(dialog.cancel_button.winfo_manager(), "grid")
        self.assertIs(dialog._start_install, start_install)
        dialog.destroy()

    def test_dialog_keeps_normal_size_on_large_work_area(self) -> None:
        size, min_size = StudioDialog._fit_to_work_area(
            ModelDirectDownloadDialog.DIALOG_SIZE,
            ModelDirectDownloadDialog.MIN_SIZE,
            (0, 0, 1920, 1080),
        )
        self.assertEqual(size, ModelDirectDownloadDialog.DIALOG_SIZE)
        self.assertEqual(min_size, ModelDirectDownloadDialog.MIN_SIZE)


if __name__ == "__main__":
    unittest.main()
