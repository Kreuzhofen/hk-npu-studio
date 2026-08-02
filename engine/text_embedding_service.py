from __future__ import annotations

import logging
import html
import json
import re
from contextlib import nullcontext
from engine.logging_config import get_logger
from pathlib import Path
from typing import Any

import numpy as np

from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector
from engine.onnx_provider_service import OnnxProviderService
from engine.cpu_pipeline_diagnostics import current_diagnostics, diagnostic_session_run

logger = get_logger("TextEmbeddingService")


def _bytes_to_unicode() -> dict[int, str]:
    byte_values = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("¡"), ord("¬") + 1))
        + list(range(ord("®"), ord("ÿ") + 1))
    )
    unicode_values = byte_values[:]
    offset = 0
    for value in range(256):
        if value not in byte_values:
            byte_values.append(value)
            unicode_values.append(256 + offset)
            offset += 1
    return dict(zip(byte_values, map(chr, unicode_values)))


class _LocalClipTokenizer:
    """Minimal CLIP BPE tokenizer backed only by package-local artifacts."""

    _PATTERN = re.compile(
        r"<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|"
        r"[^\W\d_]+|\d+|(?:[^\s\w]|_)+",
        re.IGNORECASE,
    )

    def __init__(self, tokenizer_path: Path) -> None:
        self.encoder = json.loads((tokenizer_path / "vocab.json").read_text(encoding="utf-8"))
        merge_lines = (tokenizer_path / "merges.txt").read_text(encoding="utf-8").splitlines()
        merges = [tuple(line.split()) for line in merge_lines if line and not line.startswith("#")]
        self.bpe_ranks = dict(zip(merges, range(len(merges))))
        self.byte_encoder = _bytes_to_unicode()
        self.cache: dict[str, str] = {}

        config = json.loads((tokenizer_path / "tokenizer_config.json").read_text(encoding="utf-8"))
        self.bos_token_id = int(config.get("bos_token_id", 49406))
        self.eos_token_id = int(config.get("eos_token_id", 49407))
        self.pad_token_id = int(config.get("pad_token_id", self.eos_token_id))

    @staticmethod
    def _pairs(word: tuple[str, ...]) -> set[tuple[str, str]]:
        return set(zip(word, word[1:]))

    def _bpe(self, token: str) -> str:
        cached = self.cache.get(token)
        if cached is not None:
            return cached
        word = tuple(token[:-1]) + (token[-1] + "</w>",)
        pairs = self._pairs(word)
        while pairs:
            pair = min(pairs, key=lambda item: self.bpe_ranks.get(item, float("inf")))
            if pair not in self.bpe_ranks:
                break
            first, second = pair
            merged: list[str] = []
            index = 0
            while index < len(word):
                try:
                    found = word.index(first, index)
                except ValueError:
                    merged.extend(word[index:])
                    break
                merged.extend(word[index:found])
                index = found
                if index < len(word) - 1 and word[index + 1] == second:
                    merged.append(first + second)
                    index += 2
                else:
                    merged.append(word[index])
                    index += 1
            word = tuple(merged)
            if len(word) == 1:
                break
            pairs = self._pairs(word)
        result = " ".join(word)
        self.cache[token] = result
        return result

    def encode(self, text: str, max_length: int) -> list[int]:
        cleaned = re.sub(r"\s+", " ", html.unescape(html.unescape(text))).strip().lower()
        ids = [self.bos_token_id]
        for token in self._PATTERN.findall(cleaned):
            encoded = "".join(self.byte_encoder[value] for value in token.encode("utf-8"))
            ids.extend(self.encoder[piece] for piece in self._bpe(encoded).split(" "))
        ids.append(self.eos_token_id)
        if len(ids) >= max_length:
            ids = ids[:max_length]
            ids[-1] = self.eos_token_id
        else:
            ids.extend([self.pad_token_id] * (max_length - len(ids)))
        return ids


class TextEmbeddingService:
    """
    Model-independent service for prompt tokenization and text encoder execution.
    The legacy single-encoder API remains available, while SDXL dual encoder
    conditioning uses tokenizer/tokenizer_2 and named ONNX outputs.
    """

    SEQUENCE_LENGTH = 77
    PRIMARY_WIDTH = 768
    SECONDARY_WIDTH = 1280

    def __init__(self, package: ModelRuntimePackage) -> None:
        self.package = package
        self._tokenizer_cache: dict[str, Any] = {}

    def _onnx_type_to_numpy(self, item_type: str) -> np.dtype:
        if not item_type or not isinstance(item_type, str):
            return np.float32
        lowered = item_type.lower()
        if "float" in lowered:
            return np.float32
        if "int64" in lowered:
            return np.int64
        if "int32" in lowered:
            return np.int32
        if "double" in lowered:
            return np.float64
        if "bool" in lowered:
            return np.bool_
        return np.float32

    def tokenize(self, prompt: str) -> list[int]:
        """Tokenize prompt through the primary tokenizer for legacy callers."""
        return self._tokenize_with_component(prompt, "tokenizer")

    def _tokenize_with_component(self, prompt: str, component_name: str) -> list[int]:
        """Tokenize prompt with the model's own tokenizer and exact SDXL padding."""
        tokenizer_path = self.package.get_component_path(component_name)
        fallback_used = False
        effective_component = component_name
        if component_name == "tokenizer_2" and (
            not tokenizer_path or not Path(tokenizer_path).exists()
        ):
            tokenizer_path = self.package.get_component_path("tokenizer")
            fallback_used = True
            effective_component = "tokenizer"

        logger.info(
            "[TextEmbeddingService] Resolving %s from: '%s'",
            component_name,
            tokenizer_path,
        )

        try:
            from transformers import AutoTokenizer

            if tokenizer_path and Path(tokenizer_path).exists():
                cache_key = str(Path(tokenizer_path).resolve())
                tokenizer = self._tokenizer_cache.get(cache_key)
                if tokenizer is None:
                    tokenizer = AutoTokenizer.from_pretrained(
                        tokenizer_path,
                        local_files_only=True,
                    )
                    self._tokenizer_cache[cache_key] = tokenizer
                    logger.info(
                        "[TextEmbeddingService] Cached HuggingFace tokenizer: %s",
                        cache_key,
                    )

                encoded = tokenizer(
                    prompt,
                    padding="max_length",
                    max_length=self.SEQUENCE_LENGTH,
                    truncation=True,
                    return_attention_mask=False,
                    return_tensors="np",
                )
                tokens = encoded["input_ids"][0].astype(np.int64).tolist()
                source = "tokenizer fallback" if fallback_used else component_name
                logger.info(
                    "[TextEmbeddingService] Used real HuggingFace %s.",
                    source,
                )
                return tokens
        except (ImportError, ModuleNotFoundError) as exc:
            logger.debug(
                "[TextEmbeddingService] Transformers unavailable for %s: %s",
                component_name,
                exc,
            )

        if not tokenizer_path or not Path(tokenizer_path).is_dir():
            raise RuntimeError(f"Tokenizer-Verzeichnis fehlt: {tokenizer_path}")
        try:
            cache_key = str(Path(tokenizer_path).resolve())
            tokenizer = self._tokenizer_cache.get(cache_key)
            if tokenizer is None:
                tokenizer = _LocalClipTokenizer(Path(tokenizer_path))
                self._tokenizer_cache[cache_key] = tokenizer
            tokens = tokenizer.encode(prompt, self.SEQUENCE_LENGTH)
            logger.info("[TextEmbeddingService] Used package-local CLIP BPE for %s.", effective_component)
            return tokens
        except Exception as exc:
            raise RuntimeError(
                f"Echter CLIP-Tokenizer '{component_name}' konnte nicht geladen werden: {exc}"
            ) from exc

    def embed_prompt(self, prompt: str) -> dict[str, Any]:
        """Legacy single prompt embedding API used by existing callers."""
        result = self.embed_prompt_sdxl(prompt, "")
        return {
            "tokens": result["tokens"],
            "embeddings": result["embeddings"],
            "pooled_embeddings": result["pooled_embeddings"],
            "embedding_shape": result["embedding_shape"],
            "pooled_embedding_shape": result["pooled_embedding_shape"],
            "is_mock": result["is_mock"],
            "encoder_metadata": result["encoder_metadata"],
        }

    def embed_prompt_sdxl(self, prompt: str, negative_prompt: str = "") -> dict[str, Any]:
        """Prepare SDXL conditioning for positive and negative prompts."""
        positive = self._embed_dual_encoder(prompt)
        negative = self._embed_dual_encoder(negative_prompt or "")
        return {
            "tokens": positive["tokens"],
            "negative_tokens": negative["tokens"],
            "tokens_2": positive["tokens_2"],
            "negative_tokens_2": negative["tokens_2"],
            "embeddings": positive["embeddings"],
            "negative_embeddings": negative["embeddings"],
            "pooled_embeddings": positive["pooled_embeddings"],
            "negative_pooled_embeddings": negative["pooled_embeddings"],
            "embedding_shape": list(positive["embeddings"].shape),
            "negative_embedding_shape": list(negative["embeddings"].shape),
            "pooled_embedding_shape": list(positive["pooled_embeddings"].shape),
            "negative_pooled_embedding_shape": list(negative["pooled_embeddings"].shape),
            "is_mock": bool(positive["is_mock"] or negative["is_mock"]),
            "encoder_metadata": positive["encoder_metadata"],
            "negative_encoder_metadata": negative["encoder_metadata"],
        }

    def _embed_dual_encoder(self, prompt: str) -> dict[str, Any]:
        primary_tokens = self._tokenize_with_component(prompt, "tokenizer")
        secondary_tokens = self._tokenize_with_component(prompt, "tokenizer_2")
        primary = self._run_encoder_component("text_encoder", primary_tokens, self.PRIMARY_WIDTH)
        secondary = self._run_encoder_component("text_encoder_2", secondary_tokens, self.SECONDARY_WIDTH)

        embeddings = np.concatenate([primary["embeddings"], secondary["embeddings"]], axis=-1).astype(np.float32)
        pooled = secondary["pooled_embeddings"].astype(np.float32)
        is_mock = bool(primary["is_mock"] or secondary["is_mock"])

        logger.info("[TextEmbeddingService] SDXL embeddings shape: %s, pooled: %s", embeddings.shape, pooled.shape)
        print(f"[TextEmbeddingService] SDXL embeddings shape: {embeddings.shape}, pooled: {pooled.shape}")

        return {
            "tokens": primary_tokens,
            "tokens_2": secondary_tokens,
            "embeddings": embeddings,
            "pooled_embeddings": pooled,
            "is_mock": is_mock,
            "encoder_metadata": {
                "text_encoder": primary["metadata"],
                "text_encoder_2": secondary["metadata"],
            },
        }

    def _run_encoder_component(self, component_name: str, tokens: list[int], fallback_width: int) -> dict[str, Any]:
        component_path = self.package.get_component_path(component_name)
        metadata = OnnxComponentInspector.inspect(component_name, component_path)
        token_array = np.array([tokens], dtype=np.int64)

        if not self.package.is_fully_ready() or not component_path or not Path(component_path).is_file():
            raise RuntimeError(
                f"Realer Text-Encoder '{component_name}' ist nicht verfügbar: {component_path}"
            )

        session = None
        diagnostics = current_diagnostics()
        prefix = "[TEXT ENCODER 1]" if component_name == "text_encoder" else "[TEXT ENCODER 2]"
        phase_name = "Text Encoder 1" if component_name == "text_encoder" else "Text Encoder 2"
        try:
            phase_context = diagnostics.phase(prefix, phase_name, model_path=component_path) if diagnostics else nullcontext()
            with phase_context:
                session = OnnxProviderService.create_session(component_path, component_name)
                inputs = self._build_encoder_inputs(session, token_array)
                output_names = [item.name for item in session.get_outputs()]
                values = diagnostic_session_run(
                    session, output_names, inputs, phase=phase_name,
                    component_name=component_name, model_path=component_path,
                )
                outputs = dict(zip(output_names, values))
                hidden = self._resolve_hidden_output(component_name, outputs, fallback_width)
                pooled = self._resolve_pooled_output(component_name, outputs, hidden, fallback_width)
            metadata["session_providers"] = OnnxProviderService.session_providers(session)
            return {
                "embeddings": hidden,
                "pooled_embeddings": pooled,
                "is_mock": False,
                "metadata": metadata,
            }
        except Exception as exc:
            logger.exception("[TextEmbeddingService] %s execution failed", component_name)
            raise RuntimeError(
                f"Reale CPU-Ausführung von '{component_name}' fehlgeschlagen: {exc}"
            ) from exc
        finally:
            OnnxProviderService.release_session(session)
    def _build_encoder_inputs(
        self,
        session: Any,
        token_array: np.ndarray,
    ) -> dict[str, np.ndarray]:
        inputs: dict[str, np.ndarray] = {}
        batch_size, sequence_length = token_array.shape

        for item in session.get_inputs():
            name = item.name
            lowered = name.lower()

            item_type = getattr(item, "type", None) or "tensor(int64)"
            dtype = self._onnx_type_to_numpy(item_type)

            if "position_ids" in lowered or "position" in lowered:
                position_ids = np.arange(
                    sequence_length,
                    dtype=dtype,
                )[None, :]
                inputs[name] = np.repeat(position_ids, batch_size, axis=0)
            elif "attention_mask" in lowered or "mask" in lowered:
                inputs[name] = np.ones_like(token_array, dtype=dtype)
            elif "input_ids" in lowered or lowered == "input_ids":
                inputs[name] = token_array.astype(dtype)
            elif "input" in lowered or "ids" in lowered:
                inputs[name] = token_array.astype(dtype)
            else:
                raise RuntimeError(
                    f"Unbekannter Text-Encoder-Input '{name}' "
                    f"mit Shape {item.shape}; keine Nullwerte eingesetzt."
                )

        return inputs

    def _resolve_hidden_output(
        self,
        component_name: str,
        outputs: dict[str, Any],
        fallback_width: int,
    ) -> np.ndarray:
        """
        SDXL uses the penultimate CLIP hidden state for prompt conditioning.
        Never prefer last_hidden_state when exported hidden_states are available.
        """
        hidden_candidates: list[tuple[int, str, np.ndarray]] = []

        for name, value in outputs.items():
            lowered = name.lower()
            if "hidden_states" not in lowered:
                continue

            suffix = lowered.rsplit(".", 1)[-1]
            try:
                index = int(suffix)
            except ValueError:
                continue

            hidden = self._as_hidden_states(value, fallback_width)
            if hidden.shape[-1] == fallback_width:
                hidden_candidates.append((index, name, hidden))

        if hidden_candidates:
            hidden_candidates.sort(key=lambda item: item[0])
            selected = (
                hidden_candidates[-2]
                if len(hidden_candidates) >= 2
                else hidden_candidates[-1]
            )
            logger.info(
                "[TextEmbeddingService] %s selected SDXL penultimate output: %s",
                component_name,
                selected[1],
            )
            print(
                f"[TextEmbeddingService] {component_name} selected "
                f"SDXL penultimate output: {selected[1]}"
            )
            return selected[2].astype(np.float32)

        for name in ("last_hidden_state",):
            if name in outputs:
                hidden = self._as_hidden_states(outputs[name], fallback_width)
                if hidden.shape[-1] == fallback_width:
                    logger.warning(
                        "[TextEmbeddingService] %s has no exported hidden_states; "
                        "falling back to %s",
                        component_name,
                        name,
                    )
                    return hidden.astype(np.float32)

        raise RuntimeError(
            f"Text-Encoder '{component_name}' lieferte keine kompatiblen Hidden States."
        )

    def _resolve_pooled_output(self, component_name: str, outputs: dict[str, Any], hidden: np.ndarray, fallback_width: int) -> np.ndarray:
        preferred = ["text_embeds", "pooler_output"] if component_name == "text_encoder_2" else ["pooler_output", "text_embeds"]
        for name in preferred:
            if name in outputs:
                array = np.asarray(outputs[name])
                if array.ndim == 2:
                    return array.astype(np.float32)

        pooled = hidden.mean(axis=1).astype(np.float32)
        if pooled.shape[-1] == fallback_width:
            return pooled
        return np.zeros((1, fallback_width), dtype=np.float32)

    def _as_hidden_states(self, output: Any, fallback_width: int) -> np.ndarray:
        array = np.asarray(output)
        if array.ndim == 3:
            return array.astype(np.float32)
        if array.ndim == 2:
            return np.repeat(array[:, None, :], self.SEQUENCE_LENGTH, axis=1).astype(np.float32)
        return np.zeros((1, self.SEQUENCE_LENGTH, fallback_width), dtype=np.float32)

    def _normalize_token_length(self, tokens: list[int]) -> list[int]:
        if len(tokens) < self.SEQUENCE_LENGTH:
            return tokens + [49407] * (self.SEQUENCE_LENGTH - len(tokens))
        return tokens[: self.SEQUENCE_LENGTH]

    def _zeros_for_shape(self, shape: list[Any], dtype: Any) -> np.ndarray:
        resolved = [1 if isinstance(value, str) or value is None or value < 0 else int(value) for value in shape]
        return np.zeros(resolved, dtype=dtype)
