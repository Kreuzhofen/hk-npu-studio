from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from engine.model_runtime_package import ModelRuntimePackage
from engine.onnx_component_inspector import OnnxComponentInspector

logger = logging.getLogger("TextEmbeddingService")


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

    def tokenize(self, prompt: str) -> list[int]:
        """Tokenize prompt through the primary tokenizer for legacy callers."""
        return self._tokenize_with_component(prompt, "tokenizer")

    def _tokenize_with_component(self, prompt: str, component_name: str) -> list[int]:
        """Tokenize prompt with a specific tokenizer component and fallback safely."""
        tokenizer_path = self.package.get_component_path(component_name)
        fallback_used = False
        effective_component = component_name
        if component_name == "tokenizer_2" and (not tokenizer_path or not Path(tokenizer_path).exists()):
            tokenizer_path = self.package.get_component_path("tokenizer")
            fallback_used = True
            effective_component = "tokenizer"

        logger.info("[TextEmbeddingService] Resolving %s from: '%s'", component_name, tokenizer_path)

        try:
            from transformers import AutoTokenizer
            if tokenizer_path and Path(tokenizer_path).exists():
                tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
                tokens = tokenizer.encode(prompt)
                source = "tokenizer fallback" if fallback_used else component_name
                logger.info("[TextEmbeddingService] Used real HuggingFace %s.", source)
                return self._normalize_token_length(tokens)
        except Exception as exc:
            logger.debug("[TextEmbeddingService] Real %s load skipped/failed: %s", component_name, exc)

        words = prompt.lower().split()
        token_ids = [49406]
        for word in words:
            token_ids.append((hash((effective_component, word)) % 39000) + 1000)
        token_ids.append(49407)
        logger.info("[TextEmbeddingService] Used native Python fallback tokenizer for %s.", component_name)
        return self._normalize_token_length(token_ids)

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

        if self.package.is_fully_ready() and component_path and Path(component_path).exists():
            try:
                import onnxruntime as ort
                session = ort.InferenceSession(component_path, providers=["CPUExecutionProvider"])
                inputs = self._build_encoder_inputs(session, token_array)
                output_names = [item.name for item in session.get_outputs()]
                outputs = dict(zip(output_names, session.run(output_names, inputs)))
                hidden = self._resolve_hidden_output(component_name, outputs, fallback_width)
                pooled = self._resolve_pooled_output(component_name, outputs, hidden, fallback_width)
                del session
                return {
                    "embeddings": hidden,
                    "pooled_embeddings": pooled,
                    "is_mock": False,
                    "metadata": metadata,
                }
            except Exception as exc:
                logger.warning("[TextEmbeddingService] %s run failed/skipped: %s", component_name, exc)
                print(f"[TextEmbeddingService] {component_name} run failed/skipped: {exc}")

        rng_seed = abs(hash((component_name, tuple(tokens[:12])))) % (2**32)
        rng = np.random.default_rng(rng_seed)
        hidden = rng.standard_normal((1, self.SEQUENCE_LENGTH, fallback_width), dtype=np.float32)
        pooled = hidden.mean(axis=1).astype(np.float32)
        return {
            "embeddings": hidden,
            "pooled_embeddings": pooled,
            "is_mock": True,
            "metadata": metadata,
        }

    def _build_encoder_inputs(self, session: Any, token_array: np.ndarray) -> dict[str, np.ndarray]:
        inputs: dict[str, np.ndarray] = {}
        for item in session.get_inputs():
            name = item.name
            lowered = name.lower()
            if "input" in lowered or "ids" in lowered:
                inputs[name] = token_array
            elif "mask" in lowered:
                inputs[name] = (token_array != 0).astype(np.int64)
            else:
                inputs[name] = self._zeros_for_shape(item.shape, np.int64)
        return inputs

    def _resolve_hidden_output(self, component_name: str, outputs: dict[str, Any], fallback_width: int) -> np.ndarray:
        preferred = ["last_hidden_state"]
        if component_name == "text_encoder_2":
            preferred.extend(["hidden_states.31", "hidden_states.32"])
        else:
            preferred.extend(["hidden_states.11", "hidden_states.12"])

        for name in preferred:
            if name in outputs:
                hidden = self._as_hidden_states(outputs[name], fallback_width)
                if hidden.shape[-1] == fallback_width:
                    return hidden

        for name, value in outputs.items():
            if name.startswith("hidden_states"):
                hidden = self._as_hidden_states(value, fallback_width)
                if hidden.shape[-1] == fallback_width:
                    return hidden
        return np.zeros((1, self.SEQUENCE_LENGTH, fallback_width), dtype=np.float32)

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
            return tokens + [0] * (self.SEQUENCE_LENGTH - len(tokens))
        return tokens[: self.SEQUENCE_LENGTH]

    def _zeros_for_shape(self, shape: list[Any], dtype: Any) -> np.ndarray:
        resolved = [1 if isinstance(value, str) or value is None or value < 0 else int(value) for value in shape]
        return np.zeros(resolved, dtype=dtype)
