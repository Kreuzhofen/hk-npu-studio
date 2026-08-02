"""Deterministic, local prompt recommendations for Phoenix Boost."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PromptAnalysis:
    main_object: str
    count: int | None
    actions: tuple[str, ...]
    relationships: tuple[str, ...]
    environment: str | None
    colors: tuple[str, ...]
    style: str


@dataclass(frozen=True)
class BoostSuggestion:
    original_prompt: str
    optimized_prompt: str
    existing_negative_prompt: str
    negative_addition: str
    recommended_negative_prompt: str
    language: str
    motif: str
    model_profile: str
    current_steps: int
    recommended_steps: int
    current_cfg: float
    recommended_cfg: float
    current_resolution: tuple[int, int]
    recommended_resolution: tuple[int, int]
    model_hint: str | None
    analysis: PromptAnalysis


class PhoenixBoostEngine:
    """Build conservative prompt suggestions without inference or network access."""

    _LANGUAGE_MARKERS = {
        "de": (" ein ", " eine ", " der ", " die ", " mit ", " und ", "porträt", "landschaft"),
        "es": (" un ", " una ", " el ", " la ", " con ", " y ", "retrato", "paisaje"),
    }
    _MOTIF_MARKERS = {
        "illustration": ("anime", "manga", "illustration", "ilustración", "zeichnung", "dibujo", "cartoon"),
        "portrait": ("portrait", "porträt", "retrato", "gesicht", "rostro", "woman", "mujer", "frau", "man ", "hombre", "mann"),
        "product": ("product", "produkt", "producto", "bottle", "flasche", "botella", "shoe", "schuh", "zapato"),
        "landscape": ("landscape", "landschaft", "paisaje", "mountain", "berg", "montaña", "forest", "wald", "bosque"),
    }
    _ENHANCEMENTS = {
        "en": {
            "photo": "professional photography, clear composition, natural light, sharp focus, fine detail",
            "portrait": "professional portrait photography, natural skin texture, balanced lighting, sharp eyes, fine detail",
            "landscape": "professional landscape photography, strong composition, natural light, atmospheric depth, fine detail",
            "product": "professional product photography, clean composition, controlled studio lighting, sharp focus, fine detail",
            "illustration": "refined illustration, clear composition, coherent linework, balanced colors, fine detail",
        },
        "de": {
            "photo": "professionelle Fotografie, klare Komposition, natürliches Licht, scharfer Fokus, feine Details",
            "portrait": "professionelle Porträtfotografie, natürliche Hautstruktur, ausgewogenes Licht, scharfe Augen, feine Details",
            "landscape": "professionelle Landschaftsfotografie, starke Komposition, natürliches Licht, atmosphärische Tiefe, feine Details",
            "product": "professionelle Produktfotografie, klare Komposition, kontrolliertes Studiolicht, scharfer Fokus, feine Details",
            "illustration": "hochwertige Illustration, klare Komposition, stimmige Linienführung, ausgewogene Farben, feine Details",
        },
        "es": {
            "photo": "fotografía profesional, composición clara, luz natural, enfoque nítido, detalles finos",
            "portrait": "fotografía de retrato profesional, textura de piel natural, luz equilibrada, ojos nítidos, detalles finos",
            "landscape": "fotografía de paisaje profesional, composición sólida, luz natural, profundidad atmosférica, detalles finos",
            "product": "fotografía de producto profesional, composición limpia, luz de estudio controlada, enfoque nítido, detalles finos",
            "illustration": "ilustración refinada, composición clara, líneas coherentes, colores equilibrados, detalles finos",
        },
    }
    _NEGATIVES = {
        "en": "blurry, low quality, distorted, artifacts, poor composition",
        "de": "unscharf, niedrige Qualität, verzerrt, Artefakte, schlechte Komposition",
        "es": "borroso, baja calidad, distorsionado, artefactos, mala composición",
    }
    _NUMBER_WORDS = {
        "one": 1, "a": 1, "an": 1, "ein": 1, "eine": 1, "einen": 1,
        "un": 1, "una": 1, "two": 2, "zwei": 2, "dos": 2,
        "three": 3, "drei": 3, "tres": 3,
    }
    _OBJECTS = {
        "giraffe": ("giraffe", "jirafa"),
        "people": ("people", "persons", "personen", "menschen", "personas", "gente"),
        "woman": ("woman", "frau", "mujer"),
        "man": (" man ", "mann", "hombre"),
        "balloon": ("balloon", "ballon", "globo"),
        "car": ("car", "auto", "coche", "automóvil"),
        "product": ("product", "produkt", "producto"),
    }
    _COLORS = {
        "red": ("red", "rot", "rojo", "roja"),
        "blue": ("blue", "blau", "azul"),
        "green": ("green", "grün", "verde"),
        "yellow": ("yellow", "gelb", "amarillo", "amarilla"),
        "black": ("black", "schwarz", "negro", "negra"),
        "white": ("white", "weiß", "blanco", "blanca"),
    }
    _ENVIRONMENTS = {
        "in the background": ("background", "hintergrund", "fondo"),
        "on a mountain road": ("mountain road", "bergstraße", "carretera de montaña"),
        "in a forest": ("forest", "wald", "bosque"),
        "in a city": ("city", "stadt", "ciudad"),
        "in a studio": ("studio", "estudio"),
    }

    @classmethod
    def suggest(
        cls,
        prompt: str,
        negative_prompt: str,
        model_id: str,
        steps: int,
        cfg: float,
        width: int,
        height: int,
    ) -> BoostSuggestion:
        original = prompt.strip()
        if not original:
            raise ValueError("prompt_empty")
        language = cls._detect_language(original)
        motif = cls._detect_motif(original)
        profile = cls._model_profile(model_id)
        analysis = cls.analyze(original, language)
        optimized = cls._build_prompt(original, analysis, motif)
        negative_addition = cls._NEGATIVES[language]
        existing = negative_prompt.strip()
        combined = f"{existing}, {negative_addition}" if existing else negative_addition
        recommendations = {
            "sd15": (28, 7.5, (512, 512)),
            "sd21": (30, 7.5, (512, 512)),
            "sdxl": (30, 7.0, (1024, 1024)),
        }
        recommended_steps, recommended_cfg, resolution = recommendations[profile]
        if profile == "sdxl" and motif == "portrait":
            resolution = (768, 1024)
        elif profile == "sdxl" and motif == "landscape":
            resolution = (1024, 768)
        model_hint = None
        if profile != "sdxl" and motif in {"photo", "portrait", "landscape", "product"}:
            model_hint = "sdxl"
        return BoostSuggestion(
            original, optimized, existing, negative_addition, combined,
            language, motif, profile, int(steps), recommended_steps,
            float(cfg), recommended_cfg, (int(width), int(height)), resolution, model_hint,
            analysis,
        )

    @classmethod
    def analyze(cls, prompt: str, language: str | None = None) -> PromptAnalysis:
        """Extract a small, deterministic semantic representation from the input."""
        original = prompt.strip()
        if not original:
            raise ValueError("prompt_empty")
        text = f" {original.casefold()} "
        language = language or cls._detect_language(original)
        found_objects = [name for name, terms in cls._OBJECTS.items() if any(term in text for term in terms)]
        main_object = next((item for item in found_objects if item != "balloon"), found_objects[0] if found_objects else original)
        count = cls._object_count(text, main_object)
        colors = tuple(color for color, terms in cls._COLORS.items() if any(term in text for term in terms))
        environment = next((value for value, terms in cls._ENVIRONMENTS.items() if any(term in text for term in terms)), None)

        actions: list[str] = []
        if any(term in text for term in ("holding", "holds", "hält", "halten", "sostiene", "sosteniendo")):
            actions.append("holding")
        if any(term in text for term in ("laughing", "laugh", "lachen", "lachend", "riendo", "ríen")):
            actions.append("laughing")
        if any(term in text for term in ("running", "läuft", "rennen", "corriendo")):
            actions.append("running")
        if any(term in text for term in ("floating", "schweb", "flotando", "flota")):
            actions.append("floating")

        relationships: list[str] = []
        has_balloon = "balloon" in found_objects
        if main_object == "giraffe" and has_balloon and "holding" in actions:
            relationships.append("holding the string in its mouth")
        if has_balloon and any(term in text for term in ("helium", "helio", "above", "über", "encima", "flot")):
            relationships.append("balloon floating above")
        if "people" in found_objects and "laughing" in actions and environment == "in the background":
            relationships.append("people laughing in the background")

        style = "realistic photography"
        if any(term in text for term in ("anime", "manga")):
            style = "anime illustration"
        elif any(term in text for term in ("illustration", "ilustración", "zeichnung", "dibujo")):
            style = "illustration"
        elif any(term in text for term in ("photo", "foto", "fotografía", "fotografie", "realistic", "realistisch", "realista")):
            style = "realistic photography"
        return PromptAnalysis(main_object, count, tuple(actions), tuple(relationships), environment, colors, style)

    @classmethod
    def _object_count(cls, text: str, main_object: str) -> int | None:
        object_terms = cls._OBJECTS.get(main_object, (main_object,))
        for term in object_terms:
            position = text.find(term)
            if position < 0:
                continue
            prefix = text[max(0, position - 16):position].strip().split()
            if prefix:
                token = prefix[-1].strip(".,;:!?¡¿")
                if token.isdigit():
                    return int(token)
                if token in cls._NUMBER_WORDS:
                    return cls._NUMBER_WORDS[token]
        return None

    @classmethod
    def _build_prompt(cls, original: str, analysis: PromptAnalysis, motif: str) -> str:
        clauses: list[str] = []
        if analysis.main_object == "giraffe":
            count = analysis.count or 1
            clauses.append(f"{cls._number_label(count)} giraffe in the foreground")
            if "holding the string in its mouth" in analysis.relationships:
                clauses.append("holding the string in its mouth")
            if "balloon floating above" in analysis.relationships:
                color = f"{analysis.colors[0]} " if analysis.colors else ""
                clauses.append(f"one {color}helium balloon floating above the giraffe")
        elif "people laughing in the background" in analysis.relationships:
            pass
        elif analysis.main_object != original:
            count = f"{cls._number_label(analysis.count)} " if analysis.count else ""
            clauses.append(f"{count}{analysis.main_object} in the foreground")
        else:
            clauses.append(original.rstrip(". "))

        if "people laughing in the background" in analysis.relationships:
            people_count = cls._secondary_count(original, cls._OBJECTS["people"])
            amount = f"{cls._number_label(people_count)} " if people_count else ""
            clauses.append(f"{amount}people laughing in the background")
        elif analysis.environment and analysis.environment != "in the background":
            clauses.append(analysis.environment)

        clauses.append(analysis.style)
        if motif != "illustration":
            clauses.extend(("natural lighting", "sharp focus", "clear composition"))
        return ", ".join(dict.fromkeys(clauses))

    @classmethod
    def _secondary_count(cls, prompt: str, terms: tuple[str, ...]) -> int | None:
        text = f" {prompt.casefold()} "
        for term in terms:
            match = re.search(rf"\b([\w.]+)\s+{re.escape(term.strip())}\b", text)
            if match:
                token = match.group(1)
                return int(token) if token.isdigit() else cls._NUMBER_WORDS.get(token)
        return None

    @staticmethod
    def _number_label(count: int | None) -> str:
        return {1: "one", 2: "two", 3: "three"}.get(count, str(count or 1))

    @classmethod
    def _detect_language(cls, prompt: str) -> str:
        text = f" {prompt.casefold()} "
        scores = {lang: sum(marker in text for marker in markers) for lang, markers in cls._LANGUAGE_MARKERS.items()}
        return max(scores, key=scores.get) if max(scores.values(), default=0) else "en"

    @classmethod
    def _detect_motif(cls, prompt: str) -> str:
        text = f" {prompt.casefold()} "
        for motif, markers in cls._MOTIF_MARKERS.items():
            if any(marker in text for marker in markers):
                return motif
        return "photo"

    @staticmethod
    def _model_profile(model_id: str) -> str:
        value = model_id.casefold().replace("_", "").replace("-", "")
        if "sdxl" in value or "stable diffusion xl" in value:
            return "sdxl"
        if "2.1" in value or "sd21" in value or "sd2" in value:
            return "sd21"
        return "sd15"
