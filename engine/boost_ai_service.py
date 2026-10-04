"""Optional Ollama-backed prompt optimization for Phoenix Boost with structural validation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import time
from urllib.request import Request, urlopen


from engine.logging_config import get_logger
from engine.boost_engine import LockedSemantics, PhoenixBoostEngine, StructuralValidator

logger = get_logger(__name__)


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
    REQUEST_TIMEOUT_SECONDS = 120.0
    MAX_OUTPUT_TOKENS = 320

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

            locked = PhoenixBoostEngine.extract_locked_semantics(prompt)
            instruction = (
                "You are the Phoenix Boost prompt optimizer for Stable Diffusion.\n"
                "Enhance the image prompt following these STRICT rules:\n"
                f"1. Prioritize the main subject ('{locked.subject}') at the start.\n"
                "2. Logically order the scene context.\n"
                "3. Strengthen the existing medium (e.g. realistic photo -> professional photography; Renaissance painting -> Renaissance oil painting, masterpiece).\n"
                "4. Add natural lighting and material quality.\n"
                "5. STRICTLY FORBIDDEN: Do NOT add new people, poses, arm/hand actions, clothing, hairstyles, props, backgrounds, or changes to style/medium/proper names.\n"
                "6. Return JSON ONLY with keys: 'primary_subject', 'optimized_prompt', 'summary'.\n\n"
                f"User Prompt: {json.dumps(prompt, ensure_ascii=False)}"
            )
            payload = json.dumps({
                "model": cls.MODEL,
                "prompt": instruction,
                "stream": False,
                "format": "json",
                "keep_alive": "30m",
                "options": {
                    "temperature": 0.1,
                    "num_predict": cls.MAX_OUTPUT_TOKENS,
                    "repeat_penalty": 1.2,
                },
            }).encode("utf-8")
            request = Request(
                f"{cls.BASE_URL}/api/generate", data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            endpoint = f"{cls.BASE_URL}/api/generate"
            logger.info(
                "Phoenix Boost AI request started | model=%s endpoint=%s timeout=%s",
                cls.MODEL, endpoint, timeout,
            )
            with urlopen(request, timeout=timeout) as response:
                http_status = getattr(response, "status", response.getcode())
                logger.info(
                    "Phoenix Boost AI HTTP response received | status=%s",
                    http_status,
                )
                envelope = json.loads(response.read().decode("utf-8"))
            content = envelope.get("response", "")
            data = json.loads(content) if isinstance(content, str) else content
            result = cls._parse_ai_data(data, prompt, locked)
            elapsed = time.perf_counter() - started
            logger.info(
                "Phoenix Boost AI request parse success | elapsed=%.2fs",
                elapsed,
            )
            return BoostAIRun(
                result, "success", elapsed,
                cls._change_summary(prompt, result.optimized_prompt, result.subject),
            )
        except (OSError, TimeoutError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            from engine.ollama_status import OllamaStatusService
            elapsed = time.perf_counter() - started
            http_status = getattr(error, "code", "N/A")
            logger.warning(
                "Phoenix Boost AI request/validation failed | model=%s endpoint=%s timeout=%s status=%s elapsed=%.2fs | exception=%s: %s",
                cls.MODEL, f"{cls.BASE_URL}/api/generate", timeout, http_status, elapsed, type(error).__name__, error,
            )
            OllamaStatusService.invalidate_cache()
            return BoostAIRun(None, "failed", elapsed)

    @classmethod
    def _model_available(cls, timeout: float) -> bool:
        with urlopen(f"{cls.BASE_URL}/api/tags", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        names = {str(model.get("name", "")) for model in payload.get("models", [])}
        return cls.MODEL in names

    @classmethod
    def _parse_ai_data(cls, data: object, prompt: str, locked: LockedSemantics) -> BoostAIResult:
        if not isinstance(data, dict):
            raise ValueError("invalid_ai_response")

        if "optimized_prompt" in data:
            opt = str(data["optimized_prompt"]).strip()
            is_valid, reason = StructuralValidator.validate(opt, locked)
            if not is_valid:
                logger.warning("Phoenix Boost AI candidate rejected by structural validation: %s | prompt=%s", reason, opt)
                raise ValueError(f"structural_validation_failed:{reason}")
            subject = str(data.get("primary_subject") or data.get("subject") or locked.subject).strip()
            analysis = PhoenixBoostEngine.analyze(prompt)
            negative = PhoenixBoostEngine.suggest(prompt, "", "", 1, 1.0, 1, 1).negative_addition
            return BoostAIResult(
                subject=subject,
                objects=(subject,),
                actions=analysis.actions,
                relationships=analysis.relationships,
                environment=locked.scene_location or "",
                optimized_prompt=opt,
                negative_prompt=negative,
                _count=locked.subject_count,
                _style=locked.style or "",
            )

        if "quality_enhancements" in data:
            return cls._parse_quality_result(data, prompt)

        return cls._parse_result(data)

    @classmethod
    def _parse_quality_result(cls, data: object, prompt: str) -> BoostAIResult:
        if not isinstance(data, dict) or set(data) != {"quality_enhancements", "summary"}:
            raise ValueError("invalid_quality_response_keys")
        raw_values = data.get("quality_enhancements")
        if not isinstance(raw_values, list) or not raw_values:
            raise ValueError("missing_quality_enhancements")
        allowed = {
            value.casefold(): value
            for value in PhoenixBoostEngine.allowed_quality_enhancements(prompt)
        }
        selected: list[str] = []
        for raw_value in raw_values:
            value = str(raw_value).strip()
            canonical = allowed.get(value.casefold())
            if canonical is None:
                raise ValueError(f"unsafe_quality_enhancement:{value}")
            if canonical not in selected:
                selected.append(canonical)
        optimized = PhoenixBoostEngine.compose_quality_prompt(prompt, selected)
        if optimized.casefold() == prompt.strip().rstrip(".,; ").casefold():
            raise ValueError("no_effective_quality_enhancement")
        analysis = PhoenixBoostEngine.analyze(prompt)
        negative = PhoenixBoostEngine.suggest(
            prompt, "", "", 1, 1.0, 1, 1
        ).negative_addition
        return BoostAIResult(
            subject=analysis.main_object,
            objects=(analysis.main_object,),
            actions=analysis.actions,
            relationships=analysis.relationships,
            environment=analysis.environment or "",
            optimized_prompt=optimized,
            negative_prompt=negative,
            _count=analysis.count,
            _style=analysis.style,
        )

    @staticmethod
    def _content_tokens(value: str) -> set[str]:
        return {
            token for token in re.findall(r"[^\W_]+|\d+", value.casefold(), re.UNICODE)
            if len(token) >= 4 or token.isdigit()
        }

    @classmethod
    def _preserves_prompt(cls, original: str, optimized: str) -> bool:
        """The deterministic composer always keeps the complete source as its prefix."""
        source = original.strip().rstrip(".,; ").casefold()
        return optimized.strip().casefold().startswith(source)

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
            "lighting", "light", "style", "cinematic", "atmosphere",
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
