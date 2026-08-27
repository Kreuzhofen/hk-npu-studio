"""
HK NPU STUDIO

Default Icon Generator

Created by Holger Kreuzhofen
Phoenix UI Resources
"""

from pathlib import Path

from PIL import Image, ImageDraw


ICON_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"
ICON_SIZE = 24

COLORS = {
    "accent": (198, 40, 40, 255),
    "text": (32, 33, 36, 255),
    "blue": (21, 101, 192, 255),
    "green": (46, 125, 50, 255),
    "orange": (249, 168, 37, 255),
}


def new_icon():
    return Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))


def save_icon(name, image):
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    image.save(ICON_DIR / name)


def icon_images():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.rectangle((4, 5, 18, 17), outline=COLORS["blue"], width=2)
    d.rectangle((7, 8, 21, 20), outline=COLORS["accent"], width=2)
    d.ellipse((10, 11, 14, 15), fill=COLORS["green"])
    return img


def icon_folder():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.rectangle((3, 7, 21, 19), outline=COLORS["orange"], width=2)
    d.rectangle((3, 5, 11, 8), fill=COLORS["orange"])
    return img


def icon_play():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.polygon([(8, 5), (8, 19), (19, 12)], fill=COLORS["green"])
    return img


def icon_stop():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 18, 18), fill=COLORS["accent"])
    return img


def icon_output():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.rectangle((5, 4, 19, 20), outline=COLORS["blue"], width=2)
    d.line((8, 14, 16, 14), fill=COLORS["blue"], width=2)
    d.polygon([(16, 14), (12, 10), (12, 18)], fill=COLORS["blue"])
    return img


def icon_plugin():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.rectangle((7, 7, 17, 17), outline=COLORS["text"], width=2)
    d.rectangle((10, 3, 14, 7), fill=COLORS["accent"])
    d.rectangle((10, 17, 14, 21), fill=COLORS["accent"])
    d.rectangle((3, 10, 7, 14), fill=COLORS["accent"])
    d.rectangle((17, 10, 21, 14), fill=COLORS["accent"])
    return img


def icon_settings():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.ellipse((6, 6, 18, 18), outline=COLORS["text"], width=2)
    d.ellipse((10, 10, 14, 14), fill=COLORS["accent"])
    return img


def icon_phoenix():
    img = new_icon()
    d = ImageDraw.Draw(img)
    d.polygon(
        [(12, 3), (20, 12), (15, 21), (12, 16), (9, 21), (4, 12)],
        fill=COLORS["accent"],
    )
    d.polygon(
        [(12, 6), (16, 12), (12, 14), (8, 12)],
        fill=(255, 255, 255, 180),
    )
    return img


def main():
    save_icon("images.png", icon_images())
    save_icon("folder.png", icon_folder())
    save_icon("play.png", icon_play())
    save_icon("stop.png", icon_stop())
    save_icon("output.png", icon_output())
    save_icon("plugin.png", icon_plugin())
    save_icon("settings.png", icon_settings())
    save_icon("phoenix.png", icon_phoenix())

    print(f"Default icons created in: {ICON_DIR}")


if __name__ == "__main__":
    main()