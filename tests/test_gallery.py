import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import json
import tkinter as tk

from controllers.gallery_model import GalleryImage, GalleryModel
from controllers.gallery_controller import GalleryController
from controllers.gallery_image_loader import ImageLoader
from widgets.phoenix.views.gallery_view import PhoenixGalleryView
from widgets.phoenix.gallery.toolbar import GalleryToolbar


class TestGalleryAndAssetLibrary(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create some test images
        self.img1_path = self.temp_dir / "image1.png"
        self.img1_path.touch()
        
        # Sidecar JSON for img1
        self.json1_path = self.temp_dir / "image1.json"
        with open(self.json1_path, "w", encoding="utf-8") as f:
            json.dump({
                "prompt": "a futuristic city, cyberpunk style",
                "model": "stable_diffusion_v2_1_qnn",
                "seed": 12345
            }, f)
            
        self.img2_path = self.temp_dir / "image2.jpg"
        self.img2_path.touch()

        # Damaged/invalid image path
        self.corrupt_img_path = self.temp_dir / "corrupt.png"
        self.corrupt_img_path.touch()
        with open(self.corrupt_img_path, "wb") as f:
            f.write(b"NOT_A_VALID_IMAGE_DATA")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_image_loader_valid_and_metadata(self):
        loader = ImageLoader()
        with patch("PIL.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.size = (512, 512)
            mock_open.return_value.__enter__.return_value = mock_img
            
            images = loader.load_folder(self.temp_dir)
            
            self.assertEqual(len(images), 3)
            
            img1 = next(img for img in images if img.filename == "image1.png")
            self.assertEqual(img1.prompt, "a futuristic city, cyberpunk style")
            self.assertEqual(img1.model_id, "stable_diffusion_v2_1_qnn")
            self.assertEqual(img1.seed, 12345)
            self.assertIsNotNone(img1.file_created_at)
            
            img2 = next(img for img in images if img.filename == "image2.jpg")
            self.assertIsNone(img2.prompt)
            self.assertIsNone(img2.seed)

    def test_image_loader_corrupt_resilience(self):
        loader = ImageLoader()
        with patch("PIL.Image.open", side_effect=IOError("Corrupted file")):
            images = loader.load_folder(self.temp_dir)
            self.assertEqual(len(images), 3)
            for img in images:
                self.assertIsNone(img.width)
                self.assertIsNone(img.height)

    def test_image_loader_reads_exif_orientation_without_transposing_pixels(self):
        loader = ImageLoader()
        with patch("PIL.Image.open") as mock_open:
            source = MagicMock()
            source.size = (4000, 3000)
            source.getexif.return_value = {274: 6}
            mock_open.return_value.__enter__.return_value = source
            image = loader._read_image(self.img2_path)
        self.assertEqual((image.width, image.height), (3000, 4000))
        self.assertFalse(source.transpose.called)

    def test_gallery_controller_operations(self):
        with patch("PIL.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.size = (512, 512)
            mock_open.return_value.__enter__.return_value = mock_img
            
            controller = GalleryController()
            controller.open_folder(self.temp_dir)
            
            self.assertEqual(controller.get_image_count(), 3)
            self.assertEqual(controller.get_status(), "Bereit")
            
            img1 = controller.visible_images[0]
            controller.select_image(img1)
            self.assertEqual(controller.get_selection_count(), 1)
            self.assertEqual(controller.selected_image, img1)
            
            controller.clear_selection()
            self.assertEqual(controller.get_selection_count(), 0)

    def test_gallery_refresh_detects_sidecar_metadata_changes(self):
        with patch("PIL.Image.open") as mock_open:
            mock_img = MagicMock()
            mock_img.size = (512, 512)
            mock_open.return_value.__enter__.return_value = mock_img
            controller = GalleryController()
            controller.open_folder(self.temp_dir)
            self.json1_path.write_text(
                json.dumps({"prompt": "updated prompt", "seed": 99}),
                encoding="utf-8",
            )

            changed = controller.refresh()
            image = next(
                item for item in controller.images if item.path == self.img1_path
            )

            self.assertTrue(changed)
            self.assertEqual("updated prompt", image.prompt)
            self.assertEqual(99, image.seed)

    def test_gallery_view_rendering_empty_state(self):
        empty_dir = Path(tempfile.mkdtemp())
        try:
            controller = GalleryController()
            controller.open_folder(empty_dir)
            self.assertEqual(controller.get_image_count(), 0)
        finally:
            shutil.rmtree(empty_dir)

    def test_gallery_output_action_opens_configured_output_directory(self):
        output_dir = self.temp_dir / "output"
        output_dir.mkdir()
        view = object.__new__(PhoenixGalleryView)

        with patch("widgets.phoenix.views.gallery_view.OUTPUT_DIR", output_dir), \
             patch("widgets.phoenix.views.gallery_view.subprocess.Popen") as mock_popen:
            view._open_output_directory()

        mock_popen.assert_called_once_with(["explorer", str(output_dir.resolve())])

    def test_gallery_output_action_label_is_localized_and_sized(self):
        root = Path(__file__).resolve().parents[1]
        expected_labels = {
            "de_DE": "Ausgabeordner öffnen",
            "en_US": "Open output folder",
            "es_ES": "Abrir carpeta de salida",
        }
        for locale, expected_label in expected_labels.items():
            data = json.loads((root / "locales" / f"{locale}.json").read_text(encoding="utf-8"))
            self.assertEqual(data["menu_open_output"], expected_label)
        self.assertGreaterEqual(GalleryToolbar.BUTTON_WIDTH_OPEN, 200)

    @patch("widgets.phoenix.gallery.thumbnail_area.ThumbnailProvider")
    def test_ui_view_initialization(self, mock_provider):
        root = tk.Tk()
        root.withdraw()
        try:
            mock_controller = MagicMock()
            mock_controller.visible_images = []
            mock_controller.selected_images = []
            mock_controller.selected_paths = set()
            mock_controller.get_image_count.return_value = 0
            mock_controller.get_selection_count.return_value = 0
            mock_controller.thumbnail_size_label = "Mittel"
            mock_controller.get_status.return_value = "Bereit"
            mock_controller.get_thumbnail_size.return_value = 124
            
            gallery_view = PhoenixGalleryView(root, controller=mock_controller)
            self.assertTrue(gallery_view.has_inspector)
            self.assertIsNotNone(gallery_view.inspector)
            self.assertIsNotNone(gallery_view.thumbnail_area)
            self.assertIsNotNone(gallery_view.status_bar)
            
            gallery_view.destroy()
        finally:
            root.destroy()
