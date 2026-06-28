"""
SnapdragonAI Studio

Import Service

Created by Holger Kreuzhofen
Phoenix Import Layer
"""

from pathlib import Path


class ImportService:

    def __init__(self):
        self.supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp",
        }

    def is_supported_image(self, path):
        return Path(path).suffix.lower() in self.supported_extensions

    def import_files(self, filenames):
        valid_files = []
        rejected_files = []

        for filename in filenames:
            path = Path(filename)

            if not path.exists():
                rejected_files.append((str(filename), "Datei nicht gefunden"))
                continue

            if path.is_dir():
                rejected_files.append((str(filename), "Ist ein Ordner"))
                continue

            if not self.is_supported_image(path):
                rejected_files.append(
                    (str(filename), "Nicht unterstütztes Bildformat")
                )
                continue

            valid_files.append(str(path.resolve()))

        return {
            "valid_files": valid_files,
            "rejected_files": rejected_files,
        }

    def import_folder(self, folder_path, recursive=True):
        folder = Path(folder_path)

        valid_files = []
        rejected_files = []

        if not folder.exists():
            rejected_files.append((str(folder_path), "Ordner nicht gefunden"))
            return {
                "valid_files": valid_files,
                "rejected_files": rejected_files,
            }

        if not folder.is_dir():
            rejected_files.append((str(folder_path), "Kein Ordner"))
            return {
                "valid_files": valid_files,
                "rejected_files": rejected_files,
            }

        if recursive:
            files = folder.rglob("*")
        else:
            files = folder.glob("*")

        for path in files:
            if not path.is_file():
                continue

            if self.is_supported_image(path):
                valid_files.append(str(path.resolve()))

        valid_files.sort()

        return {
            "valid_files": valid_files,
            "rejected_files": rejected_files,
        }