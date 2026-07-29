from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from string import Formatter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = PROJECT_ROOT / "locales"
REQUIRED_LOCALES = ("de_DE", "en_US", "es_ES")
PRODUCT_ROOTS = ("app", "controllers", "dialogs", "engine", "gui", "widgets")
UI_TEXT_KEYWORDS = {"text", "title", "message", "label"}
ALLOWED_PRODUCT_NAMES = {"RealESRGAN"}
GERMAN_WORDS = re.compile(
    r"\b(?:Abbrechen|Aktivieren|Alle|Ausgabe|Auswählen|Bearbeitet|Bereit|"
    r"Bild(?:er)?|Datei|Einstellungen|Fehler|Galerie|Generierung|Kein(?:e|en)?|"
    r"Löschen|Modell(?:e)?|Nicht|Öffnen|Ordner|Speichern|Verlauf|Warnung|"
    r"Warteschlange|Zurück)\b",
    re.IGNORECASE,
)


def load_locales() -> dict[str, dict[str, str]]:
    return {
        locale: json.loads(
            (LOCALES_DIR / f"{locale}.json").read_text(encoding="utf-8")
        )
        for locale in REQUIRED_LOCALES
    }


def placeholders(value: str) -> set[str]:
    return {
        field_name
        for _, field_name, _, _ in Formatter().parse(value)
        if field_name is not None
    }


def iter_product_files() -> list[Path]:
    files = [PROJECT_ROOT / "gui_v2.py"]
    for root_name in PRODUCT_ROOTS:
        files.extend((PROJECT_ROOT / root_name).rglob("*.py"))
    return [
        path
        for path in files
        if not path.name.endswith((".pyalt", ".pybak"))
        and "__pycache__" not in path.parts
    ]


def translation_keys() -> set[str]:
    keys: set[str] = set()
    for path in iter_product_files():
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "tr"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                keys.add(node.args[0].value)
    return keys


def hardcoded_ui_strings() -> list[str]:
    """Find direct visible text in modules reachable from the production entry point."""
    modules: dict[str, Path] = {}
    for path in iter_product_files():
        relative = path.relative_to(PROJECT_ROOT).with_suffix("")
        modules[".".join(relative.parts)] = path

    reachable: set[str] = set()
    pending = ["gui_v2"]
    while pending:
        module_name = pending.pop()
        if module_name in reachable or module_name not in modules:
            continue
        reachable.add(module_name)
        tree = ast.parse(
            modules[module_name].read_text(encoding="utf-8-sig"),
            filename=str(modules[module_name]),
        )
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        for imported_name in imported:
            parts = imported_name.split(".")
            for index in range(len(parts), 0, -1):
                candidate = ".".join(parts[:index])
                if candidate in modules:
                    pending.append(candidate)
                    break

    violations: list[str] = []
    for module_name in sorted(reachable):
        path = modules[module_name]
        tree = ast.parse(
            path.read_text(encoding="utf-8-sig"),
            filename=str(path),
        )
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.keyword)
                and node.arg in UI_TEXT_KEYWORDS
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and re.search(r"[A-Za-zÄÖÜäöüß]{2}", node.value.value)
            ):
                continue
            parent = parents.get(node.value)
            translated = False
            while parent is not None:
                if (
                    isinstance(parent, ast.Call)
                    and isinstance(parent.func, ast.Name)
                    and parent.func.id == "tr"
                ):
                    translated = True
                    break
                parent = parents.get(parent)
            if not translated and node.value.value not in ALLOWED_PRODUCT_NAMES:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.value.lineno}: "
                    f"{node.value.value!r}"
                )
    return violations


def audit() -> list[str]:
    errors: list[str] = []
    locales = load_locales()
    reference_keys = set(locales["de_DE"])

    for locale, values in locales.items():
        keys = set(values)
        missing = sorted(reference_keys - keys)
        extra = sorted(keys - reference_keys)
        if missing or extra:
            errors.append(f"{locale}: missing={missing}, extra={extra}")
        for key in reference_keys & keys:
            if placeholders(locales["de_DE"][key]) != placeholders(values[key]):
                errors.append(f"{locale}.{key}: placeholder mismatch")

    used_keys = translation_keys()
    missing_product_keys = sorted(used_keys - reference_keys)
    if missing_product_keys:
        errors.append(f"product translation keys missing: {missing_product_keys}")
    hardcoded = hardcoded_ui_strings()
    if hardcoded:
        errors.append(f"hardcoded UI strings: {hardcoded}")

    for locale in ("en_US", "es_ES"):
        for key, value in locales[locale].items():
            if GERMAN_WORDS.search(value):
                errors.append(f"{locale}.{key}: German text detected: {value!r}")
    return errors


def main() -> int:
    errors = audit()
    if errors:
        print("\n".join(errors))
        return 1
    locales = load_locales()
    print(
        f"Localization audit passed: {len(locales['de_DE'])} identical keys "
        f"across {', '.join(REQUIRED_LOCALES)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
