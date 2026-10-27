"""
Tests for Sprint RC4-28: Bundled Bugfixes.
Covers:
1. Home View "Jetzt einrichten" opens Model Manager ("models").
2. SD3.5 dependency and runtime packaging includes httpx.
3. Photo-drop on "KI-Fotorestaurierung" opens photo restore workflow.
4. Photo-drop on home view does not trigger unexpected navigation to image workspace.
"""

from pathlib import Path
import tempfile
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
from PIL import Image

import config
from widgets.phoenix.views.home_view import PhoenixHomeView
from widgets.phoenix.views.photo_restore_view import PhoenixPhotoRestoreView
from widgets.phoenix.sidebar import PhoenixSidebar
from widgets.phoenix.workspace import PhoenixWorkspace
from widgets.phoenix.views.image_lab_view import PhoenixImageLabView
import gui_v2


class MockDropEvent:
    def __init__(self, data: str):
        self.data = data


class RC428BugfixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="hk_rc4_28_"))
        cls.test_img = cls.temp_dir / "restore_test.png"
        Image.new("RGB", (64, 64), color="cyan").save(cls.test_img)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    # 1. Startseite: "Jetzt einrichten" muss den Model Manager öffnen
    def test_home_setup_now_opens_model_manager(self):
        navigate = MagicMock()
        view = SimpleNamespace(_model_ready=False, _navigate=navigate)
        PhoenixHomeView._on_readiness_action(view)
        navigate.assert_called_once_with("models")

    def test_home_ready_opens_prompt(self):
        navigate = MagicMock()
        view = SimpleNamespace(_model_ready=True, _navigate=navigate)
        PhoenixHomeView._on_readiness_action(view)
        navigate.assert_called_once_with("prompt")

    # 2. SD3.5-Medium-Installation: fehlendes httpx im Installations-/Runtime-Pfad
    def test_sd35_requirements_and_packaging_include_httpx(self):
        root = Path(__file__).resolve().parents[1]

        # Check requirements-qai.txt
        req_qai = (root / "requirements-qai.txt").read_text(encoding="utf-8")
        self.assertIn("httpx", req_qai)

        # Check sd35_setup_helper.py
        helper_text = (root / "tools" / "sd35_setup_helper.py").read_text(encoding="utf-8")
        self.assertIn('"import httpx\\n"', helper_text)
        self.assertIn('"httpx"', helper_text)

        # Check build_app.py
        build_text = (root / "tools" / "build_app.py").read_text(encoding="utf-8")
        self.assertIn('"--collect-all",\n                "httpx"', build_text)
        self.assertIn('"--hidden-import",\n                "httpx"', build_text)
        self.assertIn('"httpx",', build_text)

        # Check backend probe
        backend_text = (root / "engine" / "sd35_qai_appbuilder_backend.py").read_text(encoding="utf-8")
        self.assertIn("httpx", backend_text)

    # 3. Foto-Drop auf "KI-Fotorestaurierung" muss den Restaurierungsworkflow öffnen, nicht den allgemeinen Bild-Workspace
    def test_sidebar_restore_button_drop_opens_photo_restore(self):
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
            event = MockDropEvent(str(self.test_img))
            sidebar._on_restore_button_drop(event)
            workspace.open_photo_restore_with_image.assert_called_once_with(str(self.test_img))
        finally:
            sidebar.destroy()
            workspace.destroy()

    def test_photo_restore_view_drop_loads_image(self):
        view = PhoenixPhotoRestoreView(self.root)
        try:
            event = MockDropEvent(str(self.test_img))
            view._on_file_drop(event)
            self.assertEqual(view.input_path, self.test_img.resolve())
            self.assertIn(self.test_img.name, view.status_label.cget("text"))
        finally:
            view.destroy()

    def test_image_lab_card_drop_opens_photo_restore(self):
        navigated = []
        lab_view = PhoenixImageLabView.__new__(PhoenixImageLabView)
        tk.Frame.__init__(lab_view, self.root)
        lab_view.on_navigate = navigated.append
        try:
            card = lab_view._create_feature_card(
                lab_view,
                column=0,
                title="AI Fotorestaurierung",
                badge="FiDeSR Strong",
                badge_color="#22c55e",
                desc="Test description",
                action_text="Öffnen",
                target="photo_restore",
                is_primary=True,
                icon_name="sparkles",
            )
            self.assertIsNotNone(card)
        finally:
            lab_view.destroy()

    def test_workspace_open_photo_restore_with_image(self):
        workspace = PhoenixWorkspace.__new__(PhoenixWorkspace)
        tk.Frame.__init__(workspace, self.root)
        workspace.controller = None
        workspace._views = {}
        workspace.show_view = MagicMock()
        restore_view = MagicMock()
        workspace._get_or_create_view = MagicMock(return_value=restore_view)

        workspace.open_photo_restore_with_image(self.test_img)
        workspace.show_view.assert_called_once_with("inpainting")
        restore_view.load_dropped_image.assert_called_once_with(self.test_img)
        workspace.destroy()

    # 4. Foto-Drop auf der Startseite darf keine unerwartete Navigation zum Bild-Workspace auslösen
    def test_photo_drop_on_home_view_does_not_navigate_to_image(self):
        app = MagicMock()
        app._log = MagicMock()
        ws = MagicMock()
        ws.current_view = "home"
        ws._views = {}
        app.phoenix_workspace = ws
        app.load_image_files = MagicMock()

        event = MockDropEvent(str(self.test_img))
        gui_v2.SnapdragonAIStudioV2.on_drop_file(app, event)

        app.load_image_files.assert_not_called()
        ws.show_view.assert_not_called()
        ws.show_image.assert_not_called()


if __name__ == "__main__":
    unittest.main()
