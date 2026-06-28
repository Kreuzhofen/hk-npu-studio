"""
SnapdragonAI Studio

Preview Card Widget

Created by Holger Kreuzhofen
Phoenix UI
"""

from tkinter import ttk

from widgets.base_card import BaseCard


class PreviewCard(BaseCard):
    """
    Widget zur Anzeige einer Bildvorschau.
    """

    def __init__(self, master):
        super().__init__(master, "Vorschau")

        self.preview_label = ttk.Label(
            self,
            text="Keine Vorschau verfügbar",
            anchor="center",
            justify="center",
        )

        self.preview_label.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15,
        )

    def clear(self):
        """
        Setzt die Vorschau zurück.
        """

        self.preview_label.configure(
            text="Keine Vorschau verfügbar",
            image="",
        )

    def set_text(self, text: str):
        """
        Zeigt einen Hinweistext an.
        """

        self.preview_label.configure(
            text=text,
            image="",
        )

    def set_image(self, image):
        """
        Zeigt ein Bild in der Vorschau an.
        """

        self.preview_label.configure(
            image=image,
            text="",
        )

        # Referenz behalten, damit Tkinter das Bild
        # nicht vom Garbage Collector entfernen lässt.
        self.preview_label.image = image