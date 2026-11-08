"""
HK NPU STUDIO – Phoenix Prompt Engine
Component: PromptIntentParser

Parses natural language image editing prompts into structured editing intents,
target objects, material/color attributes, spatial constraints, and execution modes.

Created by Senior Software Engineer (Antigravity / Gemini)
Chief Software Architect: ChatGPT
Product Owner: Holger Kreuzhofen
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class IntentCategory(str, Enum):
    """Supported core intent categories for prompt-driven image editing."""
    MATERIAL_TRANSFORM = "MATERIAL_TRANSFORM"
    COLOR_TRANSFORM = "COLOR_TRANSFORM"
    OBJECT_REMOVAL = "OBJECT_REMOVAL"
    GLOBAL_ATMOSPHERE = "GLOBAL_ATMOSPHERE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ParsedIntent:
    """Structured representation of a user's natural language edit prompt."""
    intent: IntentCategory
    target_object: str | None
    modification: str | None
    source_material: str | None
    target_material: str | None
    source_color: str | None
    target_color: str | None
    spatial_hint: str | None
    mode: str  # "LOCAL" or "GLOBAL"
    is_confident: bool
    confidence_score: float  # 0.0 to 1.0
    raw_prompt: str
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["intent"] = self.intent.value
        return data


class PromptIntentParser:
    """
    Deterministic rule-based semantic parser for German and English image editing commands.
    Extracts structured intent, attributes, and spatial hints without external cloud AI dependencies.
    """

    # Supported Material Keywords (DE & EN)
    MATERIALS = {
        "leder": "leather",
        "lederjacke": "leather",
        "leather": "leather",
        "marmor": "marble",
        "marble": "marble",
        "gold": "gold",
        "24k gold": "gold",
        "messing": "brass",
        "antik-messing": "antique_brass",
        "brass": "brass",
        "kupfer": "copper",
        "copper": "copper",
        "chrom": "chrome",
        "chrome": "chrome",
        "silber": "silver",
        "silver": "silver",
        "holz": "wood",
        "wood": "wood",
        "glas": "glass",
        "glass": "glass",
        "keramik": "ceramic",
        "porzellan": "porcelain",
        "ceramic": "ceramic",
        "porcelain": "porcelain",
        "stoff": "fabric",
        "textil": "textile",
        "fabric": "fabric",
        "seide": "silk",
        "silk": "silk",
        "wolle": "wool",
        "wool": "wool",
        "metall": "metal",
        "metal": "metal",
        "kunststoff": "plastic",
        "plastik": "plastic",
        "plastic": "plastic",
    }

    # Supported Color Keywords (DE & EN)
    COLORS = {
        "rot": "red",
        "rote": "red",
        "roter": "red",
        "rotes": "red",
        "roten": "red",
        "red": "red",
        "blau": "blue",
        "blaue": "blue",
        "blauer": "blue",
        "blaues": "blue",
        "blauen": "blue",
        "blue": "blue",
        "grün": "green",
        "gruen": "green",
        "grüne": "green",
        "grüner": "green",
        "grünes": "green",
        "grünen": "green",
        "green": "green",
        "schwarz": "black",
        "schwarze": "black",
        "schwarzer": "black",
        "schwarzes": "black",
        "schwarzen": "black",
        "black": "black",
        "weiß": "white",
        "weiss": "white",
        "weiße": "white",
        "weisser": "white",
        "weißes": "white",
        "weißen": "white",
        "white": "white",
        "gelb": "yellow",
        "gelbe": "yellow",
        "gelber": "yellow",
        "gelbes": "yellow",
        "yellow": "yellow",
        "orange": "orange",
        "lila": "purple",
        "violett": "purple",
        "purple": "purple",
        "türkis": "cyan",
        "cyan": "cyan",
        "silber": "silver",
        "grau": "gray",
        "graue": "gray",
        "gray": "gray",
        "grey": "gray",
        "braun": "brown",
        "braune": "brown",
        "brown": "brown",
    }

    # Spatial Direction Keywords (DE & EN)
    SPATIAL_PATTERNS = [
        (r"\b(links|linke|linken|linker|linkes|on the left|to the left|left)\b", "left"),
        (r"\b(rechts|rechte|rechten|rechter|rechtes|on the right|to the right|right)\b", "right"),
        (r"\b(oben|oberer|oberen|obere|oberes|at the top|top)\b", "top"),
        (r"\b(unten|unterer|unteren|untere|unteres|at the bottom|bottom)\b", "bottom"),
        (r"\b(mitte|zentrum|zentral|in the center|in the middle|center|middle)\b", "center"),
        (r"\b(vordergrund|im vordergrund|foreground|in the foreground)\b", "foreground"),
        (r"\b(hintergrund|im hintergrund|background|in the background)\b", "background"),
    ]

    # Global Atmosphere / Lighting Keywords (DE & EN)
    GLOBAL_ATMOSPHERE_PATTERNS = [
        r"\b(sonnenuntergang|sunset|dusk|twilight|golden hour|goldene stunde)\b",
        r"\b(sonnenaufgang|sunrise|dawn|morgenröte)\b",
        r"\b(nacht|nachtszene|night|nighttime|starry night|mondschein|moonlight)\b",
        r"\b(tag|tageslicht|day|daylight|sunny day)\b",
        r"\b(regen|regnerisch|rain|rainy|regenwetter|storm|gewitter)\b",
        r"\b(schnee|winter|snow|snowy|winterlandschaft)\b",
        r"\b(herbst|autumn|fall|herbstlich)\b",
        r"\b(nebel|neblig|fog|foggy|misty)\b",
        r"\b(cyberpunk|neon|vintage|retro|dramatisches licht|dramatic lighting)\b",
    ]

    # Removal Keywords (DE & EN)
    REMOVAL_PATTERNS = [
        r"\b(entferne|entfernen|lösche|löschen|weg mit|beseitige|beseitigen|radieren)\b",
        r"\b(remove|delete|erase|clean up|take away|get rid of)\b",
    ]

    # Action / Modification Verbs
    TRANSFORM_VERBS = [
        r"\b(ändere|ändern|verändere|verändern|verwandle|verwandeln|mache|machen|wandel|wandeln|konvertiere)\b",
        r"\b(change|turn|transform|convert|make|replace|switch)\b",
        r"\b(färbe|färben|lackiere|lackieren|color|colour|paint|dye)\b",
    ]

    def parse(self, prompt: str) -> ParsedIntent:
        """
        Parse a prompt into a structured ParsedIntent.
        Guaranteed to not guess: ambiguous or unclear inputs yield UNKNOWN.
        """
        raw = prompt.strip()
        if not raw:
            return ParsedIntent(
                intent=IntentCategory.UNKNOWN,
                target_object=None,
                modification=None,
                source_material=None,
                target_material=None,
                source_color=None,
                target_color=None,
                spatial_hint=None,
                mode="LOCAL",
                is_confident=False,
                confidence_score=0.0,
                raw_prompt=raw,
                reasoning="Empty input prompt.",
            )

        text = raw.lower()

        # 1. Check for pure descriptions / conversation greetings (Do NOT guess!)
        if self._is_non_editing_prompt(text):
            return ParsedIntent(
                intent=IntentCategory.UNKNOWN,
                target_object=None,
                modification=None,
                source_material=None,
                target_material=None,
                source_color=None,
                target_color=None,
                spatial_hint=None,
                mode="LOCAL",
                is_confident=False,
                confidence_score=0.1,
                raw_prompt=raw,
                reasoning="Prompt does not express an editing intent (pure description, question, or chat greeting).",
            )

        # 2. Extract Spatial Hint if present
        spatial_hint = self._extract_spatial_hint(text)

        # 3. Check for Global Atmosphere intent
        global_match = self._match_global_atmosphere(text)
        if global_match is not None:
            return global_match

        # 4. Check for Object Removal intent
        removal_match = self._match_object_removal(text, spatial_hint, raw)
        if removal_match is not None:
            return removal_match

        # 5. Check for Material / Color Transformation
        transform_match = self._match_transformation(text, spatial_hint, raw)
        if transform_match is not None:
            return transform_match

        # 6. Fallback: No recognized structured intent -> UNKNOWN
        return ParsedIntent(
            intent=IntentCategory.UNKNOWN,
            target_object=None,
            modification=None,
            source_material=None,
            target_material=None,
            source_color=None,
            target_color=None,
            spatial_hint=spatial_hint,
            mode="LOCAL",
            is_confident=False,
            confidence_score=0.2,
            raw_prompt=raw,
            reasoning="Could not reliably detect a valid target object or transformation rule.",
        )

    def _is_non_editing_prompt(self, text: str) -> bool:
        """Filter out conversational phrases or pure T2I generation prompts."""
        chat_phrases = [
            r"^hallo\b", r"^hi\b", r"^guten tag\b", r"^wer bist du\b",
            r"^wie geht\b", r"^danke\b", r"^help\b", r"^hilfe\b"
        ]
        for pat in chat_phrases:
            if re.search(pat, text):
                return True

        # Check pure generation prompts like "Ein Foto von einem Hund", "A photo of..."
        pure_descriptions = [
            r"^(ein|eine|eines|a|an)\s+(foto|bild|photo|picture|gemälde|drawing)\s+(von|of)\b",
            r"^(foto|photo)\s+(eines|of)\b",
        ]
        for pat in pure_descriptions:
            if re.search(pat, text):
                return True

        # Check vague unspecific instructions like "mach es schöner"
        vague_phrases = [
            r"^mach\s+(es\s+)?(schöner|besser|hübscher|toll)\b",
            r"^make\s+(it\s+)?(better|nicer|prettier|cool)\b",
            r"^verändere\s+irgendwas\b",
            r"^change\s+something\b",
        ]
        for pat in vague_phrases:
            if re.search(pat, text):
                return True

        return False

    def _extract_spatial_hint(self, text: str) -> str | None:
        """Extract spatial hint (left, right, top, bottom, center, etc.)."""
        for pattern, hint in self.SPATIAL_PATTERNS:
            if re.search(pattern, text):
                return hint
        return None

    def _match_global_atmosphere(self, text: str) -> ParsedIntent | None:
        """Check if prompt describes a global atmosphere, lighting, or time-of-day shift."""
        is_global = False
        target_keyword = None
        for pat in self.GLOBAL_ATMOSPHERE_PATTERNS:
            m = re.search(pat, text)
            if m:
                is_global = True
                target_keyword = m.group(0)
                break

        if not is_global:
            return None

        # Check if the user is transforming the whole scene/day/atmosphere
        # e.g., "Mache aus dem Tag einen Sonnenuntergang", "Wandle die Szene in Nacht", "Turn day into sunset"
        source_context = None
        if "aus dem tag" in text or "vom tag" in text or "day" in text or "tag" in text:
            source_context = "Tag" if ("tag" in text or "dem tag" in text) else "Day"
        elif "aus der szene" in text or "die szene" in text or "the scene" in text:
            source_context = "Szene"
        elif "himmel" in text or "sky" in text:
            source_context = "Himmel"

        return ParsedIntent(
            intent=IntentCategory.GLOBAL_ATMOSPHERE,
            target_object=source_context or "Gesamtszene",
            modification=target_keyword.capitalize() if target_keyword else "Atmosphäre",
            source_material=None,
            target_material=None,
            source_color=None,
            target_color=None,
            spatial_hint=None,
            mode="GLOBAL",
            is_confident=True,
            confidence_score=0.95,
            raw_prompt=text,
            reasoning=f"Detected global atmosphere / illumination shift: '{target_keyword}'.",
        )

    def _match_object_removal(self, text: str, spatial_hint: str | None, raw: str) -> ParsedIntent | None:
        """Check for object removal commands (e.g., 'Entferne den Gegenstand links')."""
        has_removal_verb = False
        for pat in self.REMOVAL_PATTERNS:
            if re.search(pat, text):
                has_removal_verb = True
                break

        if not has_removal_verb:
            return None

        # Extract target object
        # e.g., "Entferne den Gegenstand links", "Remove the cup on the table"
        m = re.search(
            r"\b(?:entferne|entfernen|lösche|löschen|weg mit|remove|delete|erase)\s+(?:den|das|die|ein|eine|einen|the|a|an)?\s*([a-zäöüß0-9\-_]+)",
            text
        )
        target_obj = None
        if m:
            candidate = m.group(1).strip()
            # Ignore spatial or grammatical words as object
            if candidate not in ("links", "rechts", "oben", "unten", "left", "right", "top", "bottom", "hier", "da"):
                target_obj = candidate.capitalize()
            elif spatial_hint is not None:
                target_obj = "Objekt"

        if target_obj is None and spatial_hint is not None:
            target_obj = "Objekt"

        if target_obj is None:
            # Vague removal like "Lösche mal" without any object or direction -> UNKNOWN
            return ParsedIntent(
                intent=IntentCategory.UNKNOWN,
                target_object=None,
                modification="entfernen",
                source_material=None,
                target_material=None,
                source_color=None,
                target_color=None,
                spatial_hint=spatial_hint,
                mode="LOCAL",
                is_confident=False,
                confidence_score=0.4,
                raw_prompt=raw,
                reasoning="Detected removal verb but could not identify a valid target object or region.",
            )

        return ParsedIntent(
            intent=IntentCategory.OBJECT_REMOVAL,
            target_object=target_obj,
            modification="entfernen",
            source_material=None,
            target_material=None,
            source_color=None,
            target_color=None,
            spatial_hint=spatial_hint,
            mode="LOCAL",
            is_confident=True,
            confidence_score=0.95,
            raw_prompt=raw,
            reasoning=f"Identified object removal: '{target_obj}' with spatial hint '{spatial_hint}'.",
        )

    def _match_transformation(self, text: str, spatial_hint: str | None, raw: str) -> ParsedIntent | None:
        """
        Check for material or color transformation on a target object.
        Examples:
        - "Ändere die rote Jacke in eine schwarze Lederjacke."
        - "Verwandle den Holztisch in Marmor."
        - "Verändere nur die Farbe des Autos."
        """
        # Detect source and target materials
        source_mat = None
        target_mat = None
        for word, standard_mat in self.MATERIALS.items():
            # Check target material e.g. "in marmor", "in leder", "into marble", "zu gold"
            if re.search(rf"\b(in|into|zu|to)\s+(?:eine\s+|ein\s+|a\s+|an\s+)?(?:[a-z]+\s+)?{word}\b", text):
                target_mat = standard_mat
            elif re.search(rf"\b{word}\b", text):
                # Check if it appears before transition or as compound e.g. "holztisch" -> source wood
                if source_mat is None:
                    source_mat = standard_mat

        # Detect source and target colors
        source_col = None
        target_col = None
        for word, standard_col in self.COLORS.items():
            # Target color: "in blau", "into blue", "zu schwarz", "farbe in rot"
            if re.search(rf"\b(in|into|zu|to)\s+(?:eine\s+|ein\s+|a\s+|an\s+)?{word}\b", text) or \
               re.search(rf"\bfarbe\s+(?:des\s+[a-z]+\s+)?(?:in\s+)?{word}\b", text):
                target_col = standard_col
            elif re.search(rf"\b{word}\b", text):
                if source_col is None:
                    source_col = standard_col

        # Handle specific target object extraction
        # 1. Direct object lexicon lookup
        OBJECT_MAP = {
            "jacke": "Jacke", "jacket": "Jacke",
            "tisch": "Tisch", "table": "Tisch", "holztisch": "Tisch",
            "auto": "Auto", "car": "Car", "autos": "Auto", "cars": "Car",
            "kleid": "Kleid", "dress": "Kleid",
            "stuhl": "Stuhl", "chair": "Chair",
            "apfel": "Apfel", "apple": "Apfel",
            "skulptur": "Skulptur", "sculpture": "Skulptur", "glasskulptur": "Skulptur",
            "falke": "Falke", "vogel": "Vogel",
            "person": "Person", "fleck": "Fleck", "stain": "Stain",
            "kreis": "Kreis", "circle": "Kreis", "figur": "Figur", "figure": "Figur",
            "vase": "Vase", "krug": "Krug",
            "hund": "Hund", "dog": "Dog", "gegenstand": "Gegenstand", "object": "Objekt",
            "wand": "Wand", "wall": "Wand", "hintergrund": "Hintergrund",
        }
        target_obj = None
        for kw, canonical in OBJECT_MAP.items():
            if re.search(rf"\b{kw}\b", text):
                target_obj = canonical
                if "holz" in kw:
                    source_mat = "wood"
                break

        # 2. Pattern: "Farbe des/der X" / "color of X"
        if target_obj is None:
            m_color_of = re.search(r"\b(farbe|color)\s+(?:des|der|von|dem|of\s+the|of)?\s*([a-zäöüß0-9\-_]+)", text)
            if m_color_of:
                candidate = m_color_of.group(2).strip()
                if candidate not in self.COLORS and candidate not in self.MATERIALS:
                    target_obj = candidate.capitalize()

        # 3. Pattern: Verb + (Article) + (Color/Material) + Object
        if target_obj is None:
            m_obj = re.search(
                r"\b(?:ändere|verändere|verwandle|wandle|mache|färbe|lackiere|change|turn|transform|make|replace|paint|color|dye)\s+(?:den|das|die|ein|eine|einen|the|a|an)?\s*(?:[a-zäöüß]+\s+)?([a-zäöüß0-9\-_]+)",
                text
            )
            if m_obj:
                raw_obj = m_obj.group(1).strip()
                if raw_obj not in self.COLORS and raw_obj not in self.MATERIALS and raw_obj not in ("nur", "die", "das", "den", "eine", "einen", "the", "a", "an", "in", "into", "zu", "to"):
                    target_obj = raw_obj.capitalize()

        # Decide between MATERIAL_TRANSFORM and COLOR_TRANSFORM
        if target_mat is not None or (source_mat is not None and "marmor" in text or "leder" in text or "gold" in text):
            # Material transformation has priority if material is specified
            mod_desc = target_mat or "Material"
            if target_col is not None:
                mod_desc = f"{target_col} {mod_desc}"

            return ParsedIntent(
                intent=IntentCategory.MATERIAL_TRANSFORM,
                target_object=target_obj or "Objekt",
                modification=mod_desc,
                source_material=source_mat,
                target_material=target_mat,
                source_color=source_col,
                target_color=target_col,
                spatial_hint=spatial_hint,
                mode="LOCAL",
                is_confident=target_obj is not None,
                confidence_score=0.92 if target_obj else 0.70,
                raw_prompt=raw,
                reasoning=f"Identified material transformation on '{target_obj}': target_material='{target_mat}', target_color='{target_col}'.",
            )

        if "farbe" in text or "color" in text or target_col is not None or source_col is not None:
            # Color transformation
            return ParsedIntent(
                intent=IntentCategory.COLOR_TRANSFORM,
                target_object=target_obj or "Objekt",
                modification=f"Farbe {target_col}" if target_col else "Farbe",
                source_material=source_mat,
                target_material=None,
                source_color=source_col,
                target_color=target_col,
                spatial_hint=spatial_hint,
                mode="LOCAL",
                is_confident=target_obj is not None,
                confidence_score=0.90 if target_obj else 0.65,
                raw_prompt=raw,
                reasoning=f"Identified color transformation on '{target_obj}': source_color='{source_col}', target_color='{target_col}'.",
            )

        return None
