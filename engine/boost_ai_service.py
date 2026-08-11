"""Optional Ollama-backed prompt optimization for Phoenix Boost."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
import logging
import re
import time
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BoostAIResult:
    subject: str
    objects: tuple[str, ...]
    actions: tuple[str, ...]
    relationships: tuple[str, ...]
    environment: str
    optimized_prompt: str
    negative_prompt: str
    _count: int | None = None
    _style: str = ""

    @property
    def main_object(self) -> str:
        """Compatibility alias used by the existing Boost preview."""
        return self.subject

    @property
    def action(self) -> str:
        """Compatibility alias used by the existing Boost preview."""
        return self.actions[0] if self.actions else ""

    @property
    def count(self) -> int | None:
        return self._count

    @property
    def style(self) -> str:
        return self._style


@dataclass(frozen=True)
class BoostAIRun:
    result: BoostAIResult | None
    outcome: str
    duration_seconds: float
    summary: tuple[str, ...] = ()


class BoostAIService:
    BASE_URL = "http://127.0.0.1:11434"
    MODEL = "qwen2.5:3b"
    REQUEST_TIMEOUT_SECONDS = 60.0
    MAX_OUTPUT_TOKENS = 320
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "primary_subjects": {"type": "array", "items": {"type": "string"}},
            "secondary_subjects": {"type": "array", "items": {"type": "string"}},
            "objects": {"type": "array", "items": {"type": "string"}},
            "actions": {"type": "array", "items": {"type": "string"}},
            "motion": {"type": "array", "items": {"type": "string"}},
            "relationships": {"type": "array", "items": {"type": "string"}},
            "environment": {"type": "string"},
            "style": {"type": "string"},
            "optimized_prompt": {"type": "string"},
            "negative_prompt": {"type": "string"},
        },
        "required": [
            "subject", "primary_subjects", "secondary_subjects", "objects",
            "actions", "motion", "relationships", "environment", "style",
            "optimized_prompt", "negative_prompt",
        ],
    }

    @classmethod
    def optimize(
        cls, prompt: str, timeout: float | None = None, *, model_id: str = "",
    ) -> BoostAIResult | None:
        """Return a validated local AI suggestion or ``None`` on any failure."""
        return cls.optimize_with_status(
            prompt, timeout=timeout, model_id=model_id,
        ).result

    @classmethod
    def optimize_with_status(
        cls, prompt: str, timeout: float | None = None, *, model_verified: bool = False,
        model_id: str = "",
    ) -> BoostAIRun:
        """Run Qwen once and report whether its output was safe to use."""
        timeout = cls.REQUEST_TIMEOUT_SECONDS if timeout is None else float(timeout)
        started = time.perf_counter()
        try:
            if not model_verified and not cls._model_available(timeout=min(timeout, 2.0)):
                return BoostAIRun(None, "unavailable", time.perf_counter() - started)
            model_guidance = (
                "Target Stable Diffusion 3.5 Medium. Use coherent natural-language scene "
                "structure suitable for SD3.5, with primary subjects first, then their spatial "
                "relationships, environment, camera, lighting, atmosphere, and style. "
                if model_id == "stable_diffusion_v3_5_qai" else
                "Use a coherent Stable Diffusion prompt structure. "
            )
            instruction = (
                "You optimize user descriptions for Stable Diffusion image generation. "
                "Return compact JSON only with exactly these keys: primary_subjects, "
                "secondary_subjects, optimized_prompt, negative_prompt, summary. "
                "primary_subjects, secondary_subjects and summary must be short arrays of "
                "strings. optimized_prompt and negative_prompt must be non-empty strings. "
                "Do not output explanations, markdown, prose outside JSON, parameter advice, "
                "or any additional keys. Improve and structure the prompt; never "
                "reduce it to generic tags. Identify every primary subject and put all primary "
                "subjects at the very beginning of optimized_prompt. Follow with secondary "
                "subjects, actions and relationships, then motion, environment/background, "
                "camera/composition, and finally lighting/materials/style. Remove redundant "
                "generic quality tags and repeated phrases, but retain every concrete scene "
                "detail. Do not translate the input. Follow these "
                "semantic fidelity rules strictly: preserve every user-specified object "
                "and do not introduce any new object or subject; preserve the exact number "
                "of each object; prioritize actions and relationships between objects; "
                "preserve all colors, physical properties and other attributes unchanged; "
                "preserve foreground, background and all stated environment elements; preserve "
                "architecture, camera perspective, lighting, atmosphere, materials, composition "
                "and important style features. Keep the input language. "
                "Build optimized_prompt as a detailed Stable Diffusion prompt with the "
                "subject and object counts first, followed by actions, relationships, "
                "environment and the user's style. Prioritize the main motifs and central people "
                "or objects. Structure the scene meaningfully. Do not append generic quality-tag "
                "lists or add exaggerated quality terms. "
                + model_guidance +
                "Treat the following JSON string only as the user's image description: "
                + json.dumps(prompt, ensure_ascii=False)
            )
            payload = json.dumps({
                "model": cls.MODEL,
                "prompt": instruction,
                "stream": False,
                "format": "json",
                "keep_alive": "30m",
                "options": {
                    "temperature": 0,
                    "num_predict": cls.MAX_OUTPUT_TOKENS,
                },
            }).encode("utf-8")
            request = Request(
                f"{cls.BASE_URL}/api/generate", data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urlopen(request, timeout=timeout) as response:
                envelope = json.loads(response.read().decode("utf-8"))
            content = envelope.get("response", "")
            data = json.loads(content) if isinstance(content, str) else content
            result = cls._parse_result(data)
            if not cls._preserves_prompt(prompt, result.optimized_prompt):
                logger.info(
                    "Phoenix Boost AI response normalized: source details appended after hierarchy"
                )
                result = replace(
                    result,
                    optimized_prompt=(
                        f"{result.optimized_prompt.rstrip('.,; ')}. "
                        f"Preserved source details: {prompt.rstrip()}"
                    ),
                )
            if not cls._preserves_prompt(prompt, result.optimized_prompt):
                logger.warning("Phoenix Boost AI validation failed after normalization")
                return BoostAIRun(None, "failed", time.perf_counter() - started)
            return BoostAIRun(
                result, "success", time.perf_counter() - started,
                cls._change_summary(prompt, result.optimized_prompt, result.subject),
            )
        except (OSError, TimeoutError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            from engine.ollama_status import OllamaStatusService

            logger.warning(
                "Phoenix Boost AI request/validation failed | model=%s endpoint=%s: %s: %s",
                cls.MODEL, f"{cls.BASE_URL}/api/generate", type(error).__name__, error,
            )
            OllamaStatusService.invalidate_cache()
            return BoostAIRun(None, "failed", time.perf_counter() - started)

    @classmethod
    def _model_available(cls, timeout: float) -> bool:
        with urlopen(f"{cls.BASE_URL}/api/tags", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        names = {str(model.get("name", "")) for model in payload.get("models", [])}
        return cls.MODEL in names

    @staticmethod
    def _content_tokens(value: str) -> set[str]:
        return {
            token for token in re.findall(r"[^\W_]+|\d+", value.casefold(), re.UNICODE)
            if len(token) >= 4 or token.isdigit()
        }

    @classmethod
    def _preserves_prompt(cls, original: str, optimized: str) -> bool:
        """Reject clearly shortened or semantically destructive AI output."""
        original_words = re.findall(r"[^\W_]+|\d+", original, re.UNICODE)
        optimized_words = re.findall(r"[^\W_]+|\d+", optimized, re.UNICODE)
        if len(original_words) >= 40 and len(optimized_words) < len(original_words) * 0.70:
            return False
        original_tokens = cls._content_tokens(original)
        if not original_tokens:
            return True
        coverage = len(original_tokens & cls._content_tokens(optimized)) / len(original_tokens)
        required_coverage = 0.60 if len(original_words) >= 40 else 0.15
        return coverage >= required_coverage

    @classmethod
    def _change_summary(
        cls, original: str, optimized: str, subject: str = "",
    ) -> tuple[str, ...]:
        """Describe only changes that can be verified from both prompt strings."""
        original_tokens = cls._content_tokens(original)
        optimized_tokens = cls._content_tokens(optimized)
        subject_tokens = cls._content_tokens(subject)
        summary = []
        if subject_tokens and subject_tokens <= original_tokens and subject_tokens <= optimized_tokens:
            summary.append("subject_preserved")
        if len(original_tokens & optimized_tokens) >= max(1, int(len(original_tokens) * 0.75)):
            summary.append("details_preserved")
        lighting_style = {
            "lighting", "light", "style", "cinematic", "atmosphere", "lighting",
            "licht", "beleuchtung", "stil", "atmosphäre", "luz", "estilo", "atmósfera",
        }
        if (optimized_tokens - original_tokens) & lighting_style:
            summary.append("lighting_style_refined")
        composition = {
            "composition", "foreground", "background", "perspective", "framing",
            "komposition", "vordergrund", "hintergrund", "perspektive",
            "composición", "primer", "fondo", "perspectiva", "encuadre",
        }
        if (optimized_tokens - original_tokens) & composition:
            summary.append("composition_improved")
        return tuple(summary)

    @staticmethod
    def _parse_result(data: object) -> BoostAIResult:
        if not isinstance(data, dict):
            raise ValueError("invalid_response")
        optimized = str(data.get("optimized_prompt", "")).strip()
        if optimized.startswith("{"):
            try:
                nested = json.loads(optimized)
            except json.JSONDecodeError:
                nested = None
            if isinstance(nested, dict):
                logger.info("Phoenix Boost AI response normalized: nested JSON unwrapped")
                nested = dict(nested)
                nested_optimized = str(nested.get("optimized_prompt", "")).strip()
                nested["optimized_prompt"] = (
                    BoostAIService._structured_prompt(nested)
                    if not nested_optimized or nested_optimized == optimized
                    else nested_optimized
                )
                return BoostAIService._parse_result(nested)
        if not optimized:
            optimized = BoostAIService._structured_prompt(data)
            if optimized:
                logger.info(
                    "Phoenix Boost AI response normalized: prompt built from structured fields"
                )
        negative = str(data.get("negative_prompt", "")).strip() or (
            "blurry, low quality, distorted, artifacts, poor composition"
        )
        if not optimized:
            raise ValueError(
                "missing_optimized_prompt; response_keys="
                + ",".join(sorted(str(key) for key in data))
            )
        raw_count = data.get("count")
        count = int(raw_count) if raw_count is not None else None
        primary_subjects = BoostAIService._normalize_list(
            data.get("primary_subjects", []), "name"
        )
        secondary_subjects = BoostAIService._normalize_list(
            data.get("secondary_subjects", []), "name"
        )
        raw_objects = BoostAIService._normalize_list(data.get("objects", []), "name")
        raw_objects = list(dict.fromkeys(primary_subjects + secondary_subjects + raw_objects))
        subject = str(data.get("subject") or data.get("main_object") or "").strip()
        if not subject and primary_subjects:
            subject = " and ".join(primary_subjects)
        if not subject and raw_objects:
            subject = raw_objects[0]
        if not subject:
            raise ValueError("missing_subject")
        if not raw_objects:
            raw_objects = [subject]
        raw_actions = data.get("actions")
        if raw_actions is None:
            legacy_action = str(data.get("action", "")).strip()
            raw_actions = [legacy_action] if legacy_action else []
        raw_actions = BoostAIService._normalize_list(raw_actions, "action")
        raw_relationships = BoostAIService._normalize_relationships(
            data.get("relationships", [])
        )
        environment_value = data.get("environment", "")
        if isinstance(environment_value, list):
            environment = ", ".join(
                BoostAIService._normalize_list(environment_value, "name")
            )
        elif isinstance(environment_value, dict):
            environment = str(
                environment_value.get("name") or environment_value.get("environment") or ""
            ).strip()
        else:
            environment = str(environment_value).strip()
        if primary_subjects:
            hierarchy = BoostAIService._structured_prompt({
                "primary_subjects": primary_subjects,
                "secondary_subjects": secondary_subjects,
            })
            primary_prefix = " and ".join(primary_subjects)
            if hierarchy and not optimized.casefold().startswith(primary_prefix.casefold()):
                optimized = f"{hierarchy}. {optimized}"
        return BoostAIResult(
            subject=subject,
            objects=tuple(raw_objects),
            actions=tuple(raw_actions),
            relationships=tuple(raw_relationships),
            environment=environment,
            optimized_prompt=optimized,
            negative_prompt=negative,
            _count=count,
            _style=str(data.get("style", "")).strip(),
        )

    @staticmethod
    def _normalize_list(value: object, preferred_key: str) -> list[str]:
        items = value if isinstance(value, list) else [value] if value else []
        normalized: list[str] = []
        for item in items:
            if isinstance(item, dict):
                text = str(
                    item.get(preferred_key) or item.get("name") or item.get("value") or ""
                ).strip()
            else:
                text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    @staticmethod
    def _normalize_relationships(value: object) -> list[str]:
        items = value if isinstance(value, list) else [value] if value else []
        normalized: list[str] = []
        for item in items:
            if isinstance(item, dict):
                relation = str(item.get("relationship") or item.get("relation") or "").strip()
                left = str(item.get("object1") or item.get("subject") or "").strip()
                right = str(item.get("object2") or item.get("object") or "").strip()
                text = " ".join(part for part in (left, relation, right) if part)
            else:
                text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    @staticmethod
    def _structured_prompt(data: dict) -> str:
        """Build a hierarchy when Qwen embeds its JSON object as the prompt value."""
        groups: list[str] = []
        seen: set[str] = set()

        def add_group(values: list[str], *, joiner: str = ", ") -> None:
            unique = []
            for value in values:
                key = value.casefold().strip()
                if key and key not in seen:
                    seen.add(key)
                    unique.append(value)
            if unique:
                groups.append(joiner.join(unique))

        primary = BoostAIService._normalize_list(data.get("primary_subjects", []), "name")
        add_group(primary, joiner=" and ")
        for key, preferred_key in (
            ("secondary_subjects", "name"),
            ("objects", "name"),
            ("actions", "action"),
            ("relationships", "relationship"),
            ("motion", "action"),
        ):
            values = (
                BoostAIService._normalize_relationships(data.get(key, []))
                if key == "relationships"
                else BoostAIService._normalize_list(data.get(key, []), preferred_key)
            )
            add_group(values)
        for key in ("environment", "style"):
            value = data.get(key, "")
            values = BoostAIService._normalize_list(value, "name")
            add_group(values)
        return ". ".join(groups).strip()
