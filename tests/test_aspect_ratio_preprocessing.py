from __future__ import annotations

import unittest
import tempfile
import os
from PIL import Image, ImageDraw
import numpy as np

from engine.controlnet_canny_backend import preprocess_image_aspect_ratio, canny_edge_detector


class AspectRatioPreprocessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_preprocess_wide_image_16_9(self) -> None:
        """1. Testet das Preprocessing eines 16:9 Weitwinkelbildes"""
        # Create a 16:9 image (800x450)
        # We draw a black square in the center, and one on the left edge (should be cropped out)
        img = Image.new("RGB", (800, 450), color="white")
        draw = ImageDraw.Draw(img)
        # Center square (x: 375-425, y: 200-250) -> within center 450x450 square (x: 175-625)
        draw.rectangle([375, 200, 425, 250], fill="black")
        # Left square (x: 50-100, y: 200-250) -> should be cropped out (x < 175)
        draw.rectangle([50, 200, 100, 250], fill="black")

        processed = preprocess_image_aspect_ratio(img, (512, 512))
        self.assertEqual(processed.size, (512, 512))

        # Convert to grayscale and check pixels
        gray = processed.convert("L")
        arr = np.array(gray)

        # Center should contain the black square (value 0)
        self.assertEqual(arr[256, 256], 0)

        # Left side in the processed image should be white (value 255)
        self.assertEqual(arr[256, 10], 255)

    def test_preprocess_tall_image_9_16(self) -> None:
        """2. Testet das Preprocessing eines 9:16 Porträtbildes"""
        # Create a 9:16 image (450x800)
        # We draw a black square in the center, and one on the top edge (should be cropped out)
        img = Image.new("RGB", (450, 800), color="white")
        draw = ImageDraw.Draw(img)
        # Center square (x: 200-250, y: 375-425) -> within center 450x450 square (y: 175-625)
        draw.rectangle([200, 375, 250, 425], fill="black")
        # Top square (x: 200-250, y: 50-100) -> should be cropped out (y < 175)
        draw.rectangle([200, 50, 250, 100], fill="black")

        processed = preprocess_image_aspect_ratio(img, (512, 512))
        self.assertEqual(processed.size, (512, 512))

        # Convert to grayscale and check pixels
        gray = processed.convert("L")
        arr = np.array(gray)

        # Center should contain the black square (value 0)
        self.assertEqual(arr[256, 256], 0)

        # Top side in the processed image should be white (value 255)
        self.assertEqual(arr[10, 256], 255)

    def test_canny_edge_detector_maintains_512x512_output(self) -> None:
        """3. Prüft, dass canny_edge_detector immer ein (512, 512) Array zurückgibt"""
        # Test with 16:9 image path
        img_16_9_path = os.path.join(self.temp_dir.name, "wide.png")
        img_16_9 = Image.new("RGB", (800, 450), color="white")
        img_16_9.save(img_16_9_path)

        edges_16_9 = canny_edge_detector(img_16_9_path)
        self.assertEqual(edges_16_9.shape, (512, 512))

        # Test with 9:16 image path
        img_9_16_path = os.path.join(self.temp_dir.name, "tall.png")
        img_9_16 = Image.new("RGB", (450, 800), color="white")
        img_9_16.save(img_9_16_path)

        edges_9_16 = canny_edge_detector(img_9_16_path)
        self.assertEqual(edges_9_16.shape, (512, 512))
