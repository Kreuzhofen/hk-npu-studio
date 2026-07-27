from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


class I18nCompletenessTests(unittest.TestCase):
    def test_translation_files_keys_are_identical(self) -> None:
        """Validate that German and English translation JSON files contain the exact same keys."""
        locales_dir = Path(__file__).parent.parent / "locales"
        de_file = locales_dir / "de_DE.json"
        en_file = locales_dir / "en_US.json"
        
        self.assertTrue(de_file.is_file(), f"Missing translation file: {de_file}")
        self.assertTrue(en_file.is_file(), f"Missing translation file: {en_file}")
        
        with open(de_file, "r", encoding="utf-8") as f:
            de_keys = set(json.load(f).keys())
            
        with open(en_file, "r", encoding="utf-8") as f:
            en_keys = set(json.load(f).keys())
            
        missing_in_en = de_keys - en_keys
        missing_in_de = en_keys - de_keys
        
        self.assertEqual(
            missing_in_en, set(),
            f"Keys in de_DE.json but missing in en_US.json: {missing_in_en}"
        )
        self.assertEqual(
            missing_in_de, set(),
            f"Keys in en_US.json but missing in de_DE.json: {missing_in_de}"
        )

    def test_no_hardcoded_text_attributes_in_ui_code(self) -> None:
        """Scan active views and cards code to ensure no hardcoded UI labels are assigned directly to text attributes."""
        root_dir = Path(__file__).parent.parent
        views_dir = root_dir / "widgets" / "phoenix" / "views"
        cards_dir = root_dir / "widgets" / "phoenix" / "cards"
        
        # We target all active view files, skipping legacy/inactive files like image_view.py
        view_files = [f for f in views_dir.glob("*.py") if f.name != "image_view.py" and f.name != "__init__.py"]
        card_files = [f for f in cards_dir.glob("*.py") if f.name != "__init__.py"]
        
        all_files = view_files + card_files
        self.assertTrue(len(all_files) > 0, "No files found to scan.")
        
        # Regex to find text="something" or text='something' where 'something' starts with a letter.
        # It also covers format prefix e.g. text=f"something".
        hardcoded_pattern = re.compile(r'\btext\s*=\s*(?:f|r|fr)?["\']([a-zA-ZäöüÄÖÜß].*?)["\']')
        
        failures = []
        for file_path in all_files:
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                self.fail(f"Failed to read file {file_path}: {e}")
                
            lines = content.splitlines()
            for line_idx, line in enumerate(lines, 1):
                # Ignore comments in Python files
                if line.strip().startswith("#"):
                    continue
                
                # Check for matches
                matches = hardcoded_pattern.findall(line)
                if matches:
                    for match in matches:
                        failures.append(
                            f"File: {file_path.name}:{line_idx}\n"
                            f"  Line: {line.strip()}\n"
                            f"  Found hardcoded value: {match}"
                        )
                        
        if failures:
            failures_str = "\n\n".join(failures)
            self.fail(
                f"Found hardcoded, un-localized text values in views/cards:\n\n{failures_str}\n\n"
                f"Please wrap all UI labels in the tr() translation helper."
            )
