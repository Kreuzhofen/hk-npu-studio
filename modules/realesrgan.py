import os
from config import INPUT_DIR, OUTPUT_DIR, REALESRGAN_MODEL
from modules.realesrgan_core import upscale_tiled

def _list_images():
    images = []
    for pattern in ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.webp"):
        images.extend(INPUT_DIR.glob(pattern))
    return sorted(images)

def _choose_image(images):
    print("Gefundene Bilder:\n")
    for i, img in enumerate(images, start=1):
        print(f"{i}  {img.name}")
    choice = input("\nWelches Bild? ").strip()
    try:
        idx = int(choice) - 1
    except ValueError:
        print("Ungültige Eingabe.")
        return None
    if idx < 0 or idx >= len(images):
        print("Ungültige Auswahl.")
        return None
    return images[idx]

def run():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not REALESRGAN_MODEL.exists():
        print("Modell fehlt:", REALESRGAN_MODEL)
        return
    images = _list_images()
    if not images:
        print("Keine Bilder gefunden in:", INPUT_DIR)
        return
    image_path = _choose_image(images)
    if image_path is None:
        return
    try:
        output_path = upscale_tiled(image_path)
    except Exception as e:
        print("Fehler:", e)
        return
    if input("Bild jetzt öffnen? (j/n): ").strip().lower() == "j":
        os.startfile(output_path)
