from __future__ import annotations
import logging
from pathlib import Path
from typing import Any
import numpy as np
from engine.model_runtime_package import ModelRuntimePackage

logger = logging.getLogger("TextEmbeddingService")

class TextEmbeddingService:
    """
    Model-independent service that takes a ModelRuntimePackage, processes a prompt,
    converts it to tokens, and passes the tokens to the text encoder component
    to return a structured embedding result.
    """
    def __init__(self, package: ModelRuntimePackage) -> None:
        self.package = package

    def tokenize(self, prompt: str) -> list[int]:
        """
        Tokenize prompt. If transformers is installed, it loads a real tokenizer.
        Otherwise, it falls back to a deterministic native Python tokenizer.
        """
        tokenizer_path = self.package.get_component_path("tokenizer")
        logger.info(f"[TextEmbeddingService] Resolving tokenizer from: '{tokenizer_path}'")
        
        try:
            from transformers import AutoTokenizer
            if tokenizer_path and Path(tokenizer_path).exists():
                tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True)
                tokens = tokenizer.encode(prompt)
                logger.info("[TextEmbeddingService] Used real HuggingFace tokenizer.")
                return tokens
        except Exception as e:
            logger.debug(f"[TextEmbeddingService] Real tokenizer load skipped/failed: {e}")
            
        # Native Python deterministic word-to-ID fallback tokenizer (CLIP vocabulary simulation)
        # Standard CLIP limit is 77 tokens including SOS (49406) and EOS (49407)
        words = prompt.lower().split()
        token_ids = [49406] # SOS token
        for word in words:
            # Simple hash-based token ID generation between 1000 and 40000
            token_id = (hash(word) % 39000) + 1000
            token_ids.append(token_id)
        token_ids.append(49407) # EOS token
        
        # Pad to 77 tokens
        if len(token_ids) < 77:
            token_ids += [0] * (77 - len(token_ids))
        else:
            token_ids = token_ids[:77]
            
        logger.info("[TextEmbeddingService] Used native Python fallback tokenizer.")
        return token_ids

    def embed_prompt(self, prompt: str) -> dict[str, Any]:
        """
        Process the prompt and run it through the text encoder to get embeddings.
        """
        tokens = self.tokenize(prompt)
        text_encoder_path = self.package.get_component_path("text_encoder")
        
        logger.info(f"[TextEmbeddingService] Tokenized prompt to: {tokens[:10]}...")
        print(f"[TextEmbeddingService] Tokenized prompt to: {tokens[:10]}...")
        
        # If ONNX is available and the text encoder exists, try to run real session
        if text_encoder_path and Path(text_encoder_path).exists():
            try:
                import onnxruntime as ort
                logger.info(f"[TextEmbeddingService] Loading text encoder InferenceSession for: '{text_encoder_path}'")
                print(f"[TextEmbeddingService] Loading text encoder InferenceSession for: '{text_encoder_path}'")
                
                session = ort.InferenceSession(text_encoder_path)
                input_name = session.get_inputs()[0].name
                
                # Format tokens as batch size 1, sequence length 77
                input_data = np.array([tokens], dtype=np.int64)
                
                # Run inference
                outputs = session.run(None, {input_name: input_data})
                embeddings = outputs[0]
                
                logger.info(f"[TextEmbeddingService] ONNX Inference successful. Shape: {embeddings.shape}")
                print(f"[TextEmbeddingService] ONNX Inference successful. Shape: {embeddings.shape}")
                
                # Cleanup
                del session
                
                return {
                    "tokens": tokens,
                    "embeddings": embeddings,
                    "embedding_shape": list(embeddings.shape),
                    "is_mock": False
                }
            except Exception as e:
                logger.warning(f"[TextEmbeddingService] InferenceSession run failed/skipped: {e}")
                print(f"[TextEmbeddingService] InferenceSession run failed/skipped: {e}")
                
        # Fallback Mock embedding tensor generation (shape: 1, 77, 768 for SDXL CLIP ViT-L/14)
        mock_embedding = np.random.randn(1, 77, 768).astype(np.float32)
        logger.info(f"[TextEmbeddingService] Generated mock embeddings with shape: {mock_embedding.shape}")
        print(f"[TextEmbeddingService] Generated mock embeddings with shape: {mock_embedding.shape}")
        
        return {
            "tokens": tokens,
            "embeddings": mock_embedding,
            "embedding_shape": list(mock_embedding.shape),
            "is_mock": True
        }
