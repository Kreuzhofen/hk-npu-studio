"""Deterministic, local prompt recommendations for Phoenix Boost with locked semantics."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LockedSemantics:
    subject: str
    subject_count: int | None
    gender_age: str | None
    named_entities: tuple[str, ...]
    scene_location: str | None
    action: str | None
    medium: str
    style: str | None
    era: str | None
    explicit_objects: tuple[str, ...]
    explicit_colors: tuple[str, ...]
    explicit_composition: tuple[str, ...]
    original_prompt: str


@dataclass(frozen=True)
class PromptAnalysis:
    main_object: str
    count: int | None
    actions: tuple[str, ...]
    relationships: tuple[str, ...]
    environment: str | None
    colors: tuple[str, ...]
    style: str
    locked_semantics: LockedSemantics | None = None


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
    locked_semantics: LockedSemantics | None = None


class StructuralValidator:
    """Validates candidate prompt rewrites against locked semantics."""

    SHORT_PROMPT_WORD_LIMIT = 65
    MAX_EXPANSION_NUMERATOR = 5
    MAX_EXPANSION_DENOMINATOR = 4

    SUBJECT_ALIASES = {
        "puppy": (
            "puppy", "puppies", "welpe", "welpen", "cachorro", "cachorros",
        ),
        "kitten": (
            "kitten", "kittens", "kätzchen", "kaetzchen", "gatito", "gatitos",
        ),
        "dog": (
            "dog", "dogs", "hund", "hunde", "perro", "perros",
        ),
        "cat": (
            "cat", "cats", "katze", "katzen", "gato", "gatos",
        ),
        "girl": ("girl", "girls", "mädchen", "maedchen", "niña", "niñas"),
        "boy": ("boy", "boys", "junge", "jungen", "niño", "niños"),
        "child": ("child", "children", "kind", "kinder"),
        "woman": ("woman", "frau", "mujer"),
        "man": (" man ", "mann", "hombre"),
        "people": ("people", "persons", "personen", "menschen", "personas", "gente"),
        "giraffe": ("giraffe", "giraffes", "jirafa", "jirafas"),
        "car": ("car", "cars", "auto", "autos", "coche", "coches", "automóvil", "automóviles", "automovil", "automoviles", "sports car"),
        "balloon": ("balloon", "balloons", "ballon", "ballons", "globo", "globos"),
        "product": ("product", "products", "produkt", "produkte", "producto", "productos"),
    }

    SUBJECT_CANDIDATE_ALIASES = {
        **SUBJECT_ALIASES,
        # A general adult category can still accept a juvenile subtype. The
        # reverse is deliberately forbidden to preserve an explicit life stage.
        "dog": SUBJECT_ALIASES["dog"] + SUBJECT_ALIASES["puppy"],
        "cat": SUBJECT_ALIASES["cat"] + SUBJECT_ALIASES["kitten"],
        "child": SUBJECT_ALIASES["child"] + SUBJECT_ALIASES["girl"] + SUBJECT_ALIASES["boy"],
        "people": (
            SUBJECT_ALIASES["people"]
            + SUBJECT_ALIASES["woman"]
            + SUBJECT_ALIASES["man"]
            + SUBJECT_ALIASES["girl"]
            + SUBJECT_ALIASES["boy"]
            + SUBJECT_ALIASES["child"]
        ),
    }
    _ANIMAL_SUBJECTS = frozenset({"puppy", "dog", "kitten", "cat", "giraffe"})
    _PORTRAIT_TERMS = ("portrait", "portrait shot", "porträt", "retrato")

    POSE_SYNONYMS = {
        "sitting": ("sitting", "seated", "sitzt", "sitzend", "sentado", "sentada"),
        "lying": ("lying", "liegend", "liegt", "acostado", "tumbado"),
        "standing": ("standing", "stehend", "steht", "parado"),
        "kneeling": ("kneeling", "kniend", "kniet", "arrodillado", "arrodillada"),
        "walking": ("walking", "gehend", "geht", "caminando"),
        "running": ("running", "rennend", "rennt", "laufend", "läuft", "corriendo"),
        "jumping": ("jumping", "springend", "springt", "saltando"),
        "dancing": ("dancing", "tanzend", "tanzt", "bailando"),
        "leaning": ("leaning", "lehnend", "lehnt", "apoyado"),
        "posing": ("posing", "posierend", "posiert", "posando"),
        "waving": ("waving", "winkend", "winkt", "saludando"),
        "pointing": ("pointing", "zeigend", "zeigt", "señalando", "apuntando"),
        "reaching": ("reaching", "greifend", "reicht", "alcanzando"),
    }

    FORBIDDEN_PROPS_AND_ENTITIES = {
        # Props & furniture
        "frame", "frames", "gilded frame", "picture frame", "mirror", "chair", "chairs",
        "table", "tables", "desk", "bench", "stool", "couch", "sofa", "bed", "curtain",
        "curtains", "tripod", "softbox", "lamp", "lantern", "candle", "basket", "backpack",
        "bag", "luggage", "briefcase", "umbrella", "parasol", "glasses", "sunglasses",
        "monocle", "watch", "jewelry", "necklace", "ring", "bracelet", "earring", "earrings",
        "weapon", "sword", "gun", "knife", "shield", "cup", "mug", "glass", "bottle",
        "book", "phone", "camera", "lens", "flash", "studio equipment",
        "dslr", "photo setup", "photography setup",
        "cloth", "cloths", "blanket",
        # New clothing / accessories
        "dress", "skirt", "blouse", "shirt", "t-shirt", "jacket", "coat", "suit",
        "sweater", "hoodie", "pants", "jeans", "trousers", "shorts", "hat", "cap",
        "bonnet", "beret", "scarf", "gloves", "boots", "shoes", "heels", "sneakers",
        "sandals", "bikini", "swimsuit",
        # New body parts / poses / actions
        "hands", "hand", "arms", "arm", "legs", "leg", "feet", "foot", "fingers",
        "sitting", "seated", "sitzt", "sitzend",
        "lying", "liegend", "liegt",
        "standing", "stehend", "steht",
        "kneeling", "kniend", "kniet",
        "walking", "gehend", "geht",
        "dancing", "tanzend", "tanzt",
        "jumping", "springend", "springt",
        "leaning", "lehnend", "lehnt",
        "posing", "posierend", "posiert",
        "waving", "winkend", "winkt",
        "pointing", "zeigend", "zeigt",
        "reaching", "greifend", "reicht",
        # New unrelated environments
        "beach", "ocean", "sea", "lake", "river", "desert", "castle", "palace",
        "bedroom", "kitchen", "bathroom", "street",
    }

    @classmethod
    def _pose_group(cls, term: str) -> tuple[str, ...] | None:
        if term in cls.POSE_SYNONYMS:
            return cls.POSE_SYNONYMS[term]
        for variants in cls.POSE_SYNONYMS.values():
            if term in variants:
                return variants
        return None

    @classmethod
    def _term_in_text(cls, term: str, text: str) -> bool:
        clean = term.strip().casefold()
        if not clean:
            return False
        return bool(re.search(rf"\b{re.escape(clean)}\b", text.casefold()))

    @classmethod
    def _subject_matches(cls, subject_term: str, cand_lower: str) -> bool:
        if not subject_term:
            return True
        if cls._term_in_text(subject_term, cand_lower):
            return True
        group = None
        if subject_term in cls.SUBJECT_CANDIDATE_ALIASES:
            group = cls.SUBJECT_CANDIDATE_ALIASES[subject_term]
        else:
            for aliases in cls.SUBJECT_ALIASES.values():
                if any(cls._term_in_text(a, subject_term) or a.strip().casefold() == subject_term for a in aliases):
                    group = aliases
                    break
        if group is not None:
            return any(cls._term_in_text(alias, cand_lower) for alias in group)

        words = [w for w in re.findall(r"\w+", subject_term) if len(w) > 2]
        return any(w in cand_lower for w in words) if words else False

    @classmethod
    def validate(cls, candidate: str, locked: LockedSemantics) -> tuple[bool, str]:
        if not candidate or not candidate.strip():
            return False, "empty_candidate"

        cand_lower = candidate.casefold()
        orig_lower = locked.original_prompt.casefold()

        # 1. Named entities verification
        for ne in locked.named_entities:
            if ne.casefold() not in cand_lower:
                return False, f"named_entity_missing:{ne}"

        # 2. Subject verification
        subject_term = locked.subject.casefold().strip()
        if subject_term and not cls._subject_matches(subject_term, cand_lower):
            return False, f"subject_missing:{locked.subject}"
        if (
            subject_term in cls._ANIMAL_SUBJECTS
            and not any(term in orig_lower for term in cls._PORTRAIT_TERMS)
            and any(term in cand_lower for term in cls._PORTRAIT_TERMS)
        ):
            return False, "unrequested_animal_portrait"

        # 2b. Life stage preservation
        if locked.gender_age in ("female child", "male child", "child"):
            adult_terms = (
                "woman", "women", "frau", "frauen", "mujer", "mujeres",
                "man", "men", "mann", "männer", "maenner", "hombre", "hombres",
                "adult", "adults", "erwachsene", "erwachsener", "adulto", "adultos",
            )
            if any(cls._term_in_text(term, cand_lower) for term in adult_terms if not cls._term_in_text(term, orig_lower)):
                return False, f"unrequested_life_stage_change:{locked.gender_age}->adult"
        elif locked.gender_age in ("female adult", "male adult"):
            child_terms = (
                "girl", "girls", "mädchen", "maedchen", "niña", "niñas",
                "boy", "boys", "junge", "jungen", "niño", "niños",
                "child", "children", "kind", "kinder",
            )
            if any(cls._term_in_text(term, cand_lower) for term in child_terms if not cls._term_in_text(term, orig_lower)):
                return False, f"unrequested_life_stage_change:{locked.gender_age}->child"

        if locked.subject in ("puppy", "kitten"):
            adult_animal_terms = (
                ("dog", "dogs", "hund", "hunde", "perro", "perros")
                if locked.subject == "puppy"
                else ("cat", "cats", "katze", "katzen", "gato", "gatos")
            )
            if any(cls._term_in_text(term, cand_lower) for term in adult_animal_terms if not cls._term_in_text(term, orig_lower)):
                return False, f"unrequested_life_stage_change:{locked.subject}->adult"

        # 3. Medium & Style preservation
        if locked.medium == "art":
            forbidden_photo = ("photo", "photograph", "photorealistic", "camera", "lens", "35mm", "dslr", "cinematic", "fashion", "beauty")
            if any(term in cand_lower for term in forbidden_photo if term not in orig_lower):
                return False, "medium_conflict_art_to_photo"
        elif locked.medium == "photo":
            forbidden_art = ("painting", "oil painting", "watercolor", "illustration", "anime", "drawing", "sketch")
            if any(term in cand_lower for term in forbidden_art if term not in orig_lower):
                return False, "medium_conflict_photo_to_art"

        if locked.era and locked.era.casefold() not in cand_lower:
            return False, f"era_missing:{locked.era}"

        # 4. Location preservation
        if locked.scene_location:
            if locked.scene_location == "in the background":
                bg_terms = (
                    "background", "behind", "backdrop",
                    "hintergrund", "hinter", "fondo", "detrás", "detras",
                )
                if not any(term in cand_lower for term in bg_terms):
                    return False, f"scene_location_missing:{locked.scene_location}"
            else:
                loc_words = [w for w in re.findall(r"\w+", locked.scene_location.casefold()) if len(w) > 3]
                if loc_words and not any(w in cand_lower for w in loc_words):
                    return False, f"scene_location_missing:{locked.scene_location}"

        # 5. Check forbidden newly introduced entities / props
        cand_words = set(re.findall(r"[^\W_]+", cand_lower))
        orig_words = set(re.findall(r"[^\W_]+", orig_lower))

        for forbidden in cls.FORBIDDEN_PROPS_AND_ENTITIES:
            f_words = set(forbidden.split())
            if f_words.issubset(cand_words) and not f_words.issubset(orig_words):
                pose_variants = cls._pose_group(forbidden)
                if pose_variants is not None:
                    if any(v in orig_words for v in pose_variants) or (
                        locked.action and locked.action in pose_variants
                    ):
                        continue
                return False, f"forbidden_new_entity:{forbidden}"

        # 6. Word count limit: retain the short-prompt cap while allowing a
        # bounded 25% expansion for originals that already exceed it.
        original_word_count = len(locked.original_prompt.split())
        if original_word_count <= cls.SHORT_PROMPT_WORD_LIMIT:
            word_limit = cls.SHORT_PROMPT_WORD_LIMIT
        else:
            word_limit = (
                original_word_count * cls.MAX_EXPANSION_NUMERATOR
                + cls.MAX_EXPANSION_DENOMINATOR
                - 1
            ) // cls.MAX_EXPANSION_DENOMINATOR
        if len(candidate.split()) > word_limit:
            return False, "word_count_exceeded"

        return True, "valid"


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
    _QUALITY_ENHANCEMENTS = {
        "en": {
            "general": (
                ("fine_detail", "refined fine detail"),
                ("balanced_contrast", "balanced contrast"),
                ("local_contrast", "clean local contrast"),
                ("tonal_range", "nuanced tonal range"),
                ("subject_definition", "clear subject definition"),
                ("material_detail", "refined material detail"),
            ),
            "photo": (
                ("natural_texture", "natural texture"),
                ("exposure", "balanced exposure"),
                ("fine_detail", "refined fine detail"),
                ("local_contrast", "clean local contrast"),
                ("tonal_range", "realistic tonal range"),
                ("material_detail", "realistic material detail"),
            ),
            "portrait_photo": (
                ("skin_texture", "natural skin texture"),
                ("facial_detail", "fine facial detail"),
                ("hair_detail", "realistic hair detail"),
                ("exposure", "balanced exposure"),
                ("fine_detail", "refined fine detail"),
                ("local_contrast", "clean local contrast"),
                ("tonal_range", "realistic tonal range"),
                ("material_detail", "realistic material detail"),
            ),
            "art": (
                ("brushwork", "refined brushwork"),
                ("tonal_transitions", "nuanced tonal transitions"),
                ("surface_detail", "faithful surface detail"),
                ("balanced_contrast", "balanced contrast"),
                ("material_detail", "refined material detail"),
            ),
        },
        "de": {
            "general": (
                ("fine_detail", "verfeinerte feine Details"), ("balanced_contrast", "ausgewogener Kontrast"),
                ("local_contrast", "klarer lokaler Kontrast"), ("tonal_range", "nuancierter Tonwertumfang"),
                ("subject_definition", "klare Motivdefinition"), ("material_detail", "verfeinerte Materialdetails"),
            ),
            "photo": (
                ("natural_texture", "natürliche Textur"), ("exposure", "ausgewogene Belichtung"),
                ("fine_detail", "verfeinerte feine Details"), ("local_contrast", "klarer lokaler Kontrast"),
                ("tonal_range", "realistischer Tonwertumfang"), ("material_detail", "realistische Materialdetails"),
            ),
            "portrait_photo": (
                ("skin_texture", "natürliche Hautstruktur"), ("facial_detail", "feine Gesichtsdetails"),
                ("hair_detail", "realistische Haardetails"), ("exposure", "ausgewogene Belichtung"),
                ("fine_detail", "verfeinerte feine Details"), ("local_contrast", "klarer lokaler Kontrast"),
                ("tonal_range", "realistischer Tonwertumfang"), ("material_detail", "realistische Materialdetails"),
            ),
            "art": (
                ("brushwork", "verfeinerte Pinselführung"), ("tonal_transitions", "nuancierte Tonwertübergänge"),
                ("surface_detail", "werkgetreue Oberflächendetails"), ("balanced_contrast", "ausgewogener Kontrast"),
                ("material_detail", "verfeinerte Materialdetails"),
            ),
        },
        "es": {
            "general": (
                ("fine_detail", "detalle fino refinado"), ("balanced_contrast", "contraste equilibrado"),
                ("local_contrast", "contraste local limpio"), ("tonal_range", "rango tonal matizado"),
                ("subject_definition", "definición clara del motivo"), ("material_detail", "detalle de material refinado"),
            ),
            "photo": (
                ("natural_texture", "textura natural"), ("exposure", "exposición equilibrada"),
                ("fine_detail", "detalle fino refinado"), ("local_contrast", "contraste local limpio"),
                ("tonal_range", "rango tonal realista"), ("material_detail", "detalle de material realista"),
            ),
            "portrait_photo": (
                ("skin_texture", "textura de piel natural"), ("facial_detail", "detalle facial fino"),
                ("hair_detail", "detalle de cabello realista"), ("exposure", "exposición equilibrada"),
                ("fine_detail", "detalle fino refinado"), ("local_contrast", "contraste local limpio"),
                ("tonal_range", "rango tonal realista"), ("material_detail", "detalle de material realista"),
            ),
            "art": (
                ("brushwork", "pincelada refinada"), ("tonal_transitions", "transiciones tonales matizadas"),
                ("surface_detail", "detalle de superficie fiel"), ("balanced_contrast", "contraste equilibrado"),
                ("material_detail", "detalle de material refinado"),
            ),
        },
    }
    _QUALITY_ALIASES = {
        "fine_detail": ("fine detail", "fine details", "sharp detail", "sharp details", "feine details", "detalle fino"),
        "balanced_contrast": ("balanced contrast", "ausgewogener kontrast", "contraste equilibrado"),
        "local_contrast": ("local contrast", "lokaler kontrast", "contraste local"),
        "tonal_range": ("tonal range", "tonwertumfang", "rango tonal"),
        "subject_definition": ("subject definition", "motivdefinition", "definición clara del motivo"),
        "material_detail": ("material detail", "material details", "materialdetail", "materialdetails", "detalle de material"),
        "natural_texture": ("natural texture", "natürliche textur", "textura natural"),
        "exposure": ("balanced exposure", "ausgewogene belichtung", "exposición equilibrada"),
        "skin_texture": ("skin texture", "hautstruktur", "textura de piel", "natural skin texture"),
        "facial_detail": ("facial detail", "facial details", "gesichtsdetail", "gesichtsdetails", "detalle facial", "fine facial detail"),
        "hair_detail": ("hair detail", "hair details", "haardetail", "haardetails", "detalle de cabello", "realistic hair detail"),
        "brushwork": ("brushwork", "pinselführung", "pincelada", "refined brushwork"),
        "tonal_transitions": ("tonal transition", "tonal transitions", "tonwertübergang", "tonwertübergänge", "transiciones tonales", "nuanced tonal transitions"),
        "surface_detail": ("surface detail", "surface details", "oberflächendetail", "oberflächendetails", "detalle de superficie", "faithful surface detail"),
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
    _NAMED_ENTITIES = (
        "mona lisa", "girl with a pearl earring", "van gogh", "starry night",
        "albert einstein", "eiffel tower", "taj mahal",
    )
    _PHOTOGRAPHIC_BG_PATTERNS = (
        r"\bbokeh\b",
        r"\bdepth of field\b",
        r"\bschärfentiefe\b",
        r"\bprofundidad de campo\b",
        r"\bblur(?:red)?\b",
        r"\bunscharf\w*\b",
        r"\bborros\w*\b",
        r"\bout of focus\b",
    )
    _ANIMAL_MARKERS = (
        "puppy", "welpe", "cachorro",
        "dog", "hund", "perro",
        "cat", "katze", "gato",
        "kitten", "kätzchen", "gatito",
        "giraffe", "jirafa",
        "animal", "tier",
    )
    _OBJECTS = StructuralValidator.SUBJECT_ALIASES
    _COLORS = {
        "red": ("red", "rot", "rojo", "roja"),
        "blue": ("blue", "blau", "azul"),
        "green": ("green", "grün", "verde"),
        "yellow": ("yellow", "gelb", "amarillo", "amarilla"),
        "black": ("black", "schwarz", "negro", "negra"),
        "white": ("white", "weiß", "blanco", "blanca"),
    }
    _ENVIRONMENTS = {
        "on a mountain road": ("mountain road", "bergstraße", "carretera de montaña"),
        "in a photo studio": ("photo studio", "fotostudio", "estudio fotográfico"),
        "in a sunflower field": (
            "sunflower field", "sonnenblumenfeld", "campo de girasoles",
            "field of sunflowers", "field of tall blooming sunflowers",
        ),
        "in a forest": ("forest", "wald", "bosque"),
        "in a city": ("city", "stadt", "ciudad"),
        "in a studio": ("studio", "estudio"),
        "in the background": ("background", "hintergrund", "fondo"),
    }

    @classmethod
    def _is_photographic_background(cls, text: str) -> bool:
        """Return True if background mentions are purely photographic bokeh/depth-of-field."""
        has_bg_term = any(t in text for t in ("background", "hintergrund", "fondo"))
        if not has_bg_term:
            return False
        has_bg_entity = bool(
            re.search(
                r"\b(?:people|persons|personen|menschen|crowd|men|women|children|kinder|giraffe|jirafa)\b.*?\b(?:background|hintergrund|fondo)\b",
                text,
            )
            or re.search(
                r"\b(?:background|hintergrund|fondo)\b.*?\b(?:people|persons|personen|menschen|crowd|men|women|children|kinder|giraffe|jirafa)\b",
                text,
            )
        )
        if has_bg_entity:
            return False
        return any(re.search(pat, text) for pat in cls._PHOTOGRAPHIC_BG_PATTERNS)

    @classmethod
    def _extract_environment(cls, text: str) -> str | None:
        has_sunflower = any(term in text for term in ("sunflower", "sonnenblume", "girasol"))
        has_field = any(term in text for term in ("field", "feld", "campo"))
        if has_sunflower and has_field:
            return "in a sunflower field"

        for value, terms in cls._ENVIRONMENTS.items():
            if value == "in the background":
                continue
            if any(term in text for term in terms):
                return value

        if any(term in text for term in cls._ENVIRONMENTS["in the background"]):
            if not cls._is_photographic_background(text):
                return "in the background"

        return None

    @classmethod
    def extract_locked_semantics(cls, prompt: str, language: str | None = None) -> LockedSemantics:
        original = prompt.strip()
        if not original:
            raise ValueError("prompt_empty")
        text = f" {original.casefold()} "
        language = language or cls._detect_language(original)

        # Named entities
        named_found = tuple(
            ne.title() for ne in cls._NAMED_ENTITIES if ne in text
        )

        # Subject & Count
        found_objects = [
            name for name, terms in cls._OBJECTS.items()
            if any(StructuralValidator._term_in_text(term, text) for term in terms)
        ]
        if named_found:
            subject = named_found[0]
            count = 1
            gender_age = "female adult" if "mona lisa" in text else None
        else:
            main_object = next((item for item in found_objects if item != "balloon"), found_objects[0] if found_objects else original)
            subject = main_object
            count = cls._object_count(text, main_object)
            gender_age = None
            if any(term in text for term in ("woman", "frau", "mujer")):
                gender_age = "female adult"
            elif any(term in text for term in (" man ", "mann", "hombre")):
                gender_age = "male adult"
            elif any(term in text for term in ("girl", "mädchen", "niña")):
                gender_age = "female child"
            elif any(term in text for term in ("boy", "junge", "niño")):
                gender_age = "male child"
            elif any(term in text for term in ("child", "kind")):
                gender_age = "child"

        # Scene / Location
        environment = cls._extract_environment(text)

        # Action
        actions: list[str] = []
        if any(term in text for term in ("holding", "holds", "hält", "halten", "sostiene", "sosteniendo")):
            actions.append("holding")
        if any(term in text for term in ("laughing", "laugh", "lachen", "lachend", "riendo", "ríen")):
            actions.append("laughing")
        if any(term in text for term in ("running", "rennt", "rennend", "laufend", "läuft", "rennen", "corriendo")):
            actions.append("running")
        if any(term in text for term in ("floating", "schweb", "flotando", "flota")):
            actions.append("floating")
        if any(term in text for term in ("sitting", "seated", "sitzt", "sitzend", "sentado", "sentada")):
            actions.append("sitting")
        if any(term in text for term in ("lying", "liegend", "liegt", "acostado", "tumbado")):
            actions.append("lying")
        if any(term in text for term in ("standing", "stehend", "steht", "parado")):
            actions.append("standing")
        if any(term in text for term in ("kneeling", "kniend", "kniet", "arrodillado", "arrodillada")):
            actions.append("kneeling")
        if any(term in text for term in ("walking", "gehend", "geht", "caminando")):
            actions.append("walking")
        if any(term in text for term in ("jumping", "springend", "springt", "saltando")):
            actions.append("jumping")
        if any(term in text for term in ("dancing", "tanzend", "tanzt", "bailando")):
            actions.append("dancing")
        if any(term in text for term in ("leaning", "lehnend", "lehnt", "apoyado")):
            actions.append("leaning")
        if any(term in text for term in ("posing", "posierend", "posiert", "posando")):
            actions.append("posing")
        if any(term in text for term in ("waving", "winkend", "winkt", "saludando")):
            actions.append("waving")
        if any(term in text for term in ("pointing", "zeigend", "zeigt", "señalando", "apuntando")):
            actions.append("pointing")
        if any(term in text for term in ("reaching", "greifend", "reicht", "alcanzando")):
            actions.append("reaching")
        action = actions[0] if actions else None

        # Medium
        if any(term in text for term in ("painting", "painted", "gemälde", "malerei", "pintura", "renaissance", "oil paint")):
            medium = "art"
        elif any(term in text for term in ("illustration", "ilustración", "zeichnung", "dibujo", "anime", "manga")):
            medium = "illustration"
        elif any(term in text for term in ("photo", "foto", "fotografía", "fotografie", "realistic", "realistisch", "realista")):
            medium = "photo"
        else:
            medium = "general"

        # Style & Era
        era = "Renaissance" if "renaissance" in text else None
        style = "realistic photography" if medium == "photo" else ("art painting" if medium == "art" else None)

        # Explicit objects & colors
        explicit_objects = tuple(
            name for name, terms in cls._OBJECTS.items()
            if any(StructuralValidator._term_in_text(term, text) for term in terms)
        )
        if "sunflower" in text and "sunflower" not in explicit_objects:
            explicit_objects = explicit_objects + ("sunflower",)
        explicit_colors = tuple(color for color, terms in cls._COLORS.items() if any(term in text for term in terms))

        # Explicit composition
        composition_terms = []
        if "sharp focus" in text:
            composition_terms.append("sharp focus")
        if "close-up" in text or "closeup" in text:
            composition_terms.append("close-up")

        return LockedSemantics(
            subject=subject,
            subject_count=count,
            gender_age=gender_age,
            named_entities=named_found,
            scene_location=environment,
            action=action,
            medium=medium,
            style=style,
            era=era,
            explicit_objects=explicit_objects,
            explicit_colors=explicit_colors,
            explicit_composition=tuple(composition_terms),
            original_prompt=original,
        )

    @classmethod
    def controlled_rewrite(cls, original: str, locked: LockedSemantics, model_id: str = "") -> str:
        """Deterministically synthesize a controlled, high-fidelity prompt boost."""
        language = cls._detect_language(original)
        base = original.strip().rstrip(".,; ")
        base_folded = base.casefold()
        animal_present = any(marker in base_folded for marker in cls._ANIMAL_MARKERS) or (
            locked.subject in {"puppy", "dog", "kitten", "cat", "giraffe"}
        )
        human_indicators = (
            "woman", "frau", "mujer", " man ", "mann", "hombre",
            "people", "person", "child", "kind", "girl", "boy",
            "mädchen", "junge", "niña", "niño",
        )
        person_present = bool(
            (locked.gender_age or {"woman", "man", "people", "girl", "boy", "child"}.intersection(locked.explicit_objects))
            and (not animal_present or any(term in base_folded for term in human_indicators))
        )

        additions: list[str] = []

        if language == "de":
            if locked.medium == "art" or locked.era == "Renaissance":
                additions.extend(["Renaissance-Ölgemälde", "Meisterwerk", "verfeinerte Pinselführung", "nuancierte Tonwertübergänge", "werkgetreue Oberflächendetails", "nuanciertes Sfumato", "authentische Leinwandstruktur", "ausgewogenes Chiaroscuro"])
            elif locked.medium == "photo" or "car" in (locked.subject or "") or "car" in base_folded:
                if "studio" in (locked.scene_location or "") or "studio" in base_folded:
                    if person_present:
                        additions.extend(["professionelle Porträtfotografie", "weiche Studiobeleuchtung", "ausgewogene Belichtung", "hochauflösendes Foto"])
                    else:
                        additions.extend(["professionelle Studiofotografie", "weiche Studiobeleuchtung", "ausgewogene Belichtung", "hochauflösendes Foto"])
                elif "sunflower" in (locked.scene_location or "") or "sonnenblume" in base_folded:
                    additions.extend(["professionelle Fotografie", "natürliches Tageslicht", "weiches Sonnenlicht"])
                    if person_present:
                        additions.extend(["natürliche Hautstruktur", "feine Gesichtsdetails", "realistische Haardetails"])
                    additions.extend(["scharfer Fokus", "hochauflösendes Foto"])
                elif (locked.gender_age or "porträt" in base_folded) and person_present:
                    additions.extend(["professionelle Porträtfotografie", "natürliche Belichtung", "natürliche Hautstruktur", "feine Gesichtsdetails", "realistische Haardetails", "ausgewogene Belichtung", "realistischer Tonwertumfang", "hochauflösendes Foto"])
                else:
                    additions.extend(["professionelle Fotografie", "verfeinerte feine Details", "ausgewogener Kontrast", "verfeinerte Materialdetails", "scharfer Fokus", "hochauflösendes Foto"])
            elif locked.medium == "illustration":
                additions.extend(["detaillierte Illustration", "klare Linienführung", "harmonische Farbpalette", "klare Komposition"])
            else:
                additions.extend(["verfeinerte feine Details", "ausgewogener Kontrast", "verfeinerte Materialdetails", "scharfer Fokus", "klare Komposition"])
        elif language == "es":
            if locked.medium == "art" or locked.era == "Renaissance":
                additions.extend(["óleo renacentista", "obra maestra", "pincelada refinada", "transiciones tonales matizadas", "detalle de superficie fiel", "esfumado matizado", "textura de lienzo auténtica", "claroscuro equilibrado"])
            elif locked.medium == "photo" or "car" in (locked.subject or "") or "car" in base_folded:
                if "studio" in (locked.scene_location or "") or "estudio" in base_folded:
                    if person_present:
                        additions.extend(["fotografía de retrato profesional", "iluminación suave de estudio", "exposición equilibrada", "foto de alta resolución"])
                    else:
                        additions.extend(["fotografía de estudio profesional", "iluminación suave de estudio", "exposición equilibrada", "foto de alta resolución"])
                elif "sunflower" in (locked.scene_location or "") or "girasol" in base_folded:
                    additions.extend(["fotografía profesional", "luz natural del día", "luz solar suave"])
                    if person_present:
                        additions.extend(["textura de piel natural", "detalle facial fino", "detalle de cabello realista"])
                    additions.extend(["enfoque nítido", "foto de alta resolución"])
                elif (locked.gender_age or "retrato" in base_folded) and person_present:
                    additions.extend(["fotografía de retrato profesional", "iluminación natural", "textura de piel natural", "detalle facial fino", "detalle de cabello realista", "exposición equilibrada", "rango tonal realista", "foto de alta resolución"])
                else:
                    additions.extend(["fotografía profesional", "detalle fino refinado", "contraste equilibrado", "detalle de material refinado", "enfoque nítido", "foto de alta resolución"])
            elif locked.medium == "illustration":
                additions.extend(["ilustración detallada", "trazos limpios", "paleta armoniosa", "composición limpia"])
            else:
                additions.extend(["detalle fino refinado", "contraste equilibrado", "detalle de material refinado", "enfoque nítido", "composición clara"])
        else: # en
            if locked.medium == "art" or locked.era == "Renaissance" or "mona lisa" in base_folded:
                additions.extend(["Renaissance oil painting", "masterpiece", "refined brushwork", "nuanced tonal transitions", "faithful surface detail", "nuanced sfumato", "authentic canvas texture", "balanced chiaroscuro", "rich tones"])
            elif locked.medium == "photo" or "car" in (locked.subject or "") or "car" in base_folded:
                if "studio" in (locked.scene_location or "") or "studio" in base_folded:
                    if person_present:
                        additions.extend(["professional portrait photography", "soft studio lighting", "balanced exposure", "high resolution photo"])
                    else:
                        additions.extend(["professional studio photography", "soft studio lighting", "balanced exposure", "high resolution photo"])
                elif "sunflower" in (locked.scene_location or "") or "sunflower" in base_folded:
                    additions.extend(["professional photography", "natural daylight", "soft sunlight"])
                    if person_present:
                        additions.extend(["natural skin texture", "fine facial detail", "realistic hair detail"])
                    additions.extend(["sharp focus", "high resolution photo"])
                elif "mountain road" in (locked.scene_location or "") or "car" in (locked.subject or "") or "car" in base_folded:
                    additions.extend(["professional photography", "dynamic natural lighting", "sharp focus", "refined fine detail", "balanced contrast", "refined material detail", "high resolution photo"])
                elif (locked.gender_age or "portrait" in base_folded) and person_present:
                    additions.extend(["professional portrait photography", "natural lighting", "natural skin texture", "fine facial detail", "realistic hair detail", "balanced exposure", "realistic tonal range", "high resolution photo"])
                else:
                    additions.extend(["professional photography", "natural lighting", "sharp focus", "refined fine detail", "balanced contrast", "refined material detail", "high resolution photo"])
            elif locked.medium == "illustration":
                additions.extend(["detailed illustration", "crisp linework", "harmonious palette", "clean composition"])
            else:
                additions.extend(["refined fine detail", "balanced contrast", "refined material detail", "natural lighting", "sharp focus", "clear composition"])

        # Deduplicate terms already present in the original prompt
        clean_additions: list[str] = []
        for phrase in additions:
            phrase_clean = phrase.strip()
            if phrase_clean.casefold() not in base_folded and phrase_clean not in clean_additions:
                clean_additions.append(phrase_clean)

        return f"{base}, {', '.join(clean_additions)}" if clean_additions else base

    @classmethod
    def allowed_quality_enhancements(cls, prompt: str) -> tuple[str, ...]:
        language = cls._detect_language(prompt)
        profile = cls._quality_profile(prompt)
        return tuple(text for _concept, text in cls._QUALITY_ENHANCEMENTS[language][profile])

    @classmethod
    def compose_quality_prompt(cls, original: str, enhancements: tuple[str, ...] | list[str]) -> str:
        source = original.strip()
        source_folded = source.casefold()
        allowed = {
            text.casefold(): (concept, text)
            for profiles in cls._QUALITY_ENHANCEMENTS.values()
            for entries in profiles.values()
            for concept, text in entries
        }
        additions: list[str] = []
        used_concepts: set[str] = set()
        for value in enhancements:
            entry = allowed.get(str(value).strip().casefold())
            if entry is None:
                continue
            concept, text = entry
            if concept in used_concepts or cls._quality_present(source_folded, concept):
                continue
            used_concepts.add(concept)
            additions.append(text)
        base = source.rstrip(".,; ")
        return f"{base}, {', '.join(additions)}" if additions else base

    @classmethod
    def _quality_present(cls, source: str, concept: str) -> bool:
        return any(alias in source for alias in cls._QUALITY_ALIASES.get(concept, ()))

    @classmethod
    def _quality_profile(cls, prompt: str) -> str:
        text = f" {prompt.casefold()} "
        if any(term in text for term in ("painting", "painted", "gemälde", "malerei", "pintura", "illustration", "illustración", "zeichnung", "renaissance")):
            return "art"
        is_photo = any(term in text for term in (" photo ", " photograph", "fotografie", " fotografía", " foto "))
        is_person = any(term in text for term in (
            " portrait", " porträt", " retrato", " woman", " frau", " mujer",
            " man ", " mann", " hombre", " bride", " groom", " braut", " bräutigam",
            " girl", " boy", " person", " people",
        ))
        if is_photo and is_person:
            return "portrait_photo"
        if is_photo:
            return "photo"
        return "general"

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
        locked = cls.extract_locked_semantics(original, language)
        analysis = cls.analyze(original, language)
        optimized = cls.controlled_rewrite(original, locked, model_id)
        negative_addition = ""
        existing = negative_prompt.strip()
        combined = existing
        recommendations = {
            "sd15": (28, 7.5, (512, 512)),
            "sd21": (30, 7.5, (512, 512)),
            "sd25": (30, 7.5, (768, 768)),
            "sd35": (8, 3.5, (1024, 1024)),
            "sdxl": (30, 7.0, (1024, 1024)),
        }
        recommended_steps, recommended_cfg, resolution = recommendations.get(profile, (8, 3.5, (1024, 1024)))
        if profile == "sdxl" and motif == "portrait":
            resolution = (768, 1024)
        elif profile == "sdxl" and motif == "landscape":
            resolution = (1024, 768)
        model_hint = None
        if profile in {"sd15", "sd21", "sd25"} and motif in {"photo", "portrait", "landscape", "product"}:
            model_hint = "sdxl"
        return BoostSuggestion(
            original, optimized, existing, negative_addition, combined,
            language, motif, profile, int(steps), recommended_steps,
            float(cfg), recommended_cfg, (int(width), int(height)), resolution, model_hint,
            analysis, locked_semantics=locked,
        )

    @classmethod
    def analyze(cls, prompt: str, language: str | None = None) -> PromptAnalysis:
        """Extract a small, deterministic semantic representation from the input."""
        original = prompt.strip()
        if not original:
            raise ValueError("prompt_empty")
        text = f" {original.casefold()} "
        language = language or cls._detect_language(original)
        locked = cls.extract_locked_semantics(original, language)
        found_objects = [name for name, terms in cls._OBJECTS.items() if any(term in text for term in terms)]
        main_object = next((item for item in found_objects if item != "balloon"), found_objects[0] if found_objects else original)
        count = cls._object_count(text, main_object)
        colors = tuple(color for color, terms in cls._COLORS.items() if any(term in text for term in terms))
        environment = cls._extract_environment(text)

        actions: list[str] = []
        if any(term in text for term in ("holding", "holds", "hält", "halten", "sostiene", "sosteniendo")):
            actions.append("holding")
        if any(term in text for term in ("laughing", "laugh", "lachen", "lachend", "riendo", "ríen")):
            actions.append("laughing")
        if any(term in text for term in ("running", "rennt", "rennend", "laufend", "läuft", "rennen", "corriendo")):
            actions.append("running")
        if any(term in text for term in ("floating", "schweb", "flotando", "flota")):
            actions.append("floating")
        if any(term in text for term in ("sitting", "seated", "sitzt", "sitzend", "sentado", "sentada")):
            actions.append("sitting")
        if any(term in text for term in ("lying", "liegend", "liegt", "acostado", "tumbado")):
            actions.append("lying")
        if any(term in text for term in ("standing", "stehend", "steht", "parado")):
            actions.append("standing")
        if any(term in text for term in ("kneeling", "kniend", "kniet", "arrodillado", "arrodillada")):
            actions.append("kneeling")
        if any(term in text for term in ("walking", "gehend", "geht", "caminando")):
            actions.append("walking")
        if any(term in text for term in ("jumping", "springend", "springt", "saltando")):
            actions.append("jumping")
        if any(term in text for term in ("dancing", "tanzend", "tanzt", "bailando")):
            actions.append("dancing")
        if any(term in text for term in ("leaning", "lehnend", "lehnt", "apoyado")):
            actions.append("leaning")
        if any(term in text for term in ("posing", "posierend", "posiert", "posando")):
            actions.append("posing")
        if any(term in text for term in ("waving", "winkend", "winkt", "saludando")):
            actions.append("waving")
        if any(term in text for term in ("pointing", "zeigend", "zeigt", "señalando", "apuntando")):
            actions.append("pointing")
        if any(term in text for term in ("reaching", "greifend", "reicht", "alcanzando")):
            actions.append("reaching")

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
        elif any(term in text for term in ("painting", "painted", "gemälde", "malerei", "pintura", "renaissance")):
            style = "art painting"
        elif any(term in text for term in ("photo", "foto", "fotografía", "fotografie", "realistic", "realistisch", "realista")):
            style = "realistic photography"
        return PromptAnalysis(main_object, count, tuple(actions), tuple(relationships), environment, colors, style, locked_semantics=locked)

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
        if "3.5" in value or "sd35" in value or "stablediffusionv35" in value:
            return "sd35"
        if "2.5" in value or "sd25" in value or "stablediffusionv25" in value:
            return "sd25"
        if "sdxl" in value or "stable diffusion xl" in value:
            return "sdxl"
        if "2.1" in value or "sd21" in value or "sd2" in value:
            return "sd21"
        return "sd15"
