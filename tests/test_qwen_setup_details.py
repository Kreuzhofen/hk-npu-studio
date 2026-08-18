from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from pathlib import Path
from PIL import Image

from dialogs.qwen_setup_dialog import QwenSetupDialog
from engine.theme_manager import ThemeManager


class TestQwenSetupDetails(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw() # Do not display window during tests

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_image_processing_ollama_light_theme(self) -> None:
        # Create a mock white image representing ollama.png
        img = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
        path = Path("ollama.png")
        
        # Instantiate dialog in mock state
        dialog = MagicMock(spec=QwenSetupDialog)
        
        # Test under light theme
        with patch.object(ThemeManager, "active_theme", return_value=ThemeManager.PROFESSIONAL_LIGHT):
            processed = QwenSetupDialog._process_image_for_theme(dialog, img, path)
            pixels = processed.load()
            # Opaque pixels should have become (24, 33, 44)
            self.assertEqual(pixels[0, 0], (24, 33, 44, 255))

        # Test under dark theme
        img2 = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
        with patch.object(ThemeManager, "active_theme", return_value=ThemeManager.PROFESSIONAL_DARK):
            processed2 = QwenSetupDialog._process_image_for_theme(dialog, img2, path)
            pixels2 = processed2.load()
            # Opaque pixels should remain white in dark theme
            self.assertEqual(pixels2[0, 0], (255, 255, 255, 255))

    def test_image_processing_qwen_transparency(self) -> None:
        # Create a mock image with a white background and a non-white center (representing the Qwen logo)
        img = Image.new("RGB", (20, 20), (255, 255, 255))
        pixels = img.load()
        # Draw a non-white box in the center
        for y in range(5, 15):
            for x in range(5, 15):
                pixels[x, y] = (100, 50, 150)
                
        path = Path("qwen.jpg")
        dialog = MagicMock(spec=QwenSetupDialog)
        
        processed = QwenSetupDialog._process_image_for_theme(dialog, img, path)
        pixels_out = processed.load()
        
        # Corners should be transparent
        self.assertEqual(pixels_out[0, 0][3], 0)
        self.assertEqual(pixels_out[19, 0][3], 0)
        self.assertEqual(pixels_out[0, 19][3], 0)
        self.assertEqual(pixels_out[19, 19][3], 0)
        
        # Center should remain fully opaque
        self.assertEqual(pixels_out[10, 10][3], 255)
        self.assertEqual(pixels_out[10, 10][:3], (100, 50, 150))

    def test_progress_parsing_percentage_determinate(self) -> None:
        dialog = MagicMock(spec=QwenSetupDialog)
        dialog._update_progressbar = MagicMock()
        dialog._status_lbl = MagicMock()
        dialog._desc_lbl = MagicMock()
        
        # Emulate receiving a download progress update line (containing MB)
        line = "pulling c5396e06af29:  42% ▕███████           ▏ 166 MB/397 MB  6.9 MB/s"
        QwenSetupDialog._parse_output_line(dialog, line)
        
        # Should call _update_progressbar with determinate and 42
        dialog._update_progressbar.assert_called_with("determinate", 42)

    def test_progress_parsing_cap_at_99_before_success(self) -> None:
        dialog = MagicMock(spec=QwenSetupDialog)
        dialog._update_progressbar = MagicMock()
        dialog._status_lbl = MagicMock()
        dialog._desc_lbl = MagicMock()
        
        # Emulate receiving a 100% download line for the main layer
        line = "pulling c5396e06af29: 100% ▕██████████████████▏ 397 MB"
        QwenSetupDialog._parse_output_line(dialog, line)
        
        # Should cap progress bar at 99% until success state/verification is complete
        dialog._update_progressbar.assert_called_with("determinate", 99)

    def test_progress_parsing_raw_layer_without_mb_gb(self) -> None:
        dialog = MagicMock(spec=QwenSetupDialog)
        dialog._update_progressbar = MagicMock()
        dialog._status_lbl = MagicMock()
        dialog._desc_lbl = MagicMock()
        
        # Emulate receiving a download progress update line without MB/GB units
        line = "pulling 5ee4f07cdb9b: 42%"
        QwenSetupDialog._parse_output_line(dialog, line)
        
        # Should call _update_progressbar with determinate and 42
        dialog._update_progressbar.assert_called_with("determinate", 42)

    def test_progress_parsing_raw_layer_with_mb_gb(self) -> None:
        dialog = MagicMock(spec=QwenSetupDialog)
        dialog._update_progressbar = MagicMock()
        dialog._status_lbl = MagicMock()
        dialog._desc_lbl = MagicMock()
        
        # Emulate receiving a download progress update line with MB/GB units
        line = "pulling 5ee4f07cdb9b: 42% ▕███████           ▏ 166 MB/397 MB  6.9 MB/s"
        QwenSetupDialog._parse_output_line(dialog, line)
        
        # Should call _update_progressbar with determinate and 42
        dialog._update_progressbar.assert_called_with("determinate", 42)

    def test_progress_parsing_verifying_indeterminate(self) -> None:
        dialog = MagicMock(spec=QwenSetupDialog)
        dialog._update_progressbar = MagicMock()
        dialog._status_lbl = MagicMock()
        dialog._desc_lbl = MagicMock()
        
        # Emulate verifying output
        line = "verifying sha256 digest"
        QwenSetupDialog._parse_output_line(dialog, line)
        
        dialog._update_progressbar.assert_called_with("indeterminate")


if __name__ == "__main__":
    unittest.main()
