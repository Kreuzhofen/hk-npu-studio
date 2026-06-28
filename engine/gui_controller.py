"""
SnapdragonAI Studio

GUI Controller

Created by Holger Kreuzhofen
Phoenix Controller Layer
"""

from pathlib import Path

from engine.phoenix_adapter import PhoenixAdapter


class GuiController:

    def __init__(self):
        self.adapter = PhoenixAdapter()
        self.loaded_images = []
        self.current_image = None
        self.last_output = None

        self.supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp",
        }

    def is_supported_image(self, path):
        return Path(path).suffix.lower() in self.supported_extensions

    def load_image_files(self, filenames):
        valid_files = []
        rejected_files = []

        for filename in filenames:
            path = Path(filename)

            if not path.exists():
                rejected_files.append((str(filename), "Datei nicht gefunden"))
                continue

            if not self.is_supported_image(path):
                rejected_files.append((str(filename), "Nicht unterstütztes Bildformat"))
                continue

            full_path = str(path.resolve())

            if full_path not in self.loaded_images:
                self.loaded_images.append(full_path)

            valid_files.append(full_path)

        if valid_files:
            self.current_image = valid_files[0]

        return {
            "valid_files": valid_files,
            "rejected_files": rejected_files,
        }

    def select_image(self, filename):
        path = Path(filename)

        if not path.exists():
            return False, "Datei nicht gefunden"

        if not self.is_supported_image(path):
            return False, "Nicht unterstütztes Bildformat"

        self.current_image = str(path.resolve())
        return True, self.current_image

    def get_current_image(self):
        return self.current_image

    def clear_last_output(self):
        self.last_output = None

    def set_last_output(self, output_path):
        self.last_output = output_path

    def get_last_output(self):
        return self.last_output

    def run_upscale(self, input_path):
        result = self.adapter.run(
            "image.upscale",
            input_path=input_path,
        )

        output_path = result["output_path"]
        self.last_output = output_path

        return output_path