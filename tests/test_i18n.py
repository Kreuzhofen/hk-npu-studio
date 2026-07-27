from __future__ import annotations

import unittest
from app.i18n import tr, set_language, get_current_language, get_available_languages


class I18nTests(unittest.TestCase):
    def setUp(self) -> None:
        set_language("de_DE")

    def test_default_language_is_de_de(self) -> None:
        self.assertEqual(get_current_language(), "de_DE")

    def test_german_translation_lookup(self) -> None:
        set_language("de_DE")
        self.assertEqual(tr("reference_image"), "Referenzbild")
        self.assertEqual(tr("drag_and_drop_text"), "Bild hierher ziehen oder klicken")

    def test_english_translation_lookup(self) -> None:
        set_language("en_US")
        self.assertEqual(tr("reference_image"), "Reference Image")
        self.assertEqual(tr("drag_and_drop_text"), "Drag image here or click")

    def test_variable_interpolation(self) -> None:
        set_language("de_DE")
        self.assertEqual(tr("status_prefix", status="Bereit"), "Status: Bereit")
        
        set_language("en_US")
        self.assertEqual(tr("status_prefix", status="Ready"), "Status: Ready")

    def test_key_fallback(self) -> None:
        self.assertEqual(tr("non_existent_key", default="Default Val"), "Default Val")
        self.assertEqual(tr("non_existent_key_no_default"), "non_existent_key_no_default")

    def test_available_languages(self) -> None:
        langs = get_available_languages()
        self.assertIn("de_DE", langs)
        self.assertIn("en_US", langs)


