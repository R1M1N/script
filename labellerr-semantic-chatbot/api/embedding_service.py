# api/embedding_service.py
import logging
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
from config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.device = settings.EMBEDDING_DEVICE
        self.normalize = settings.NORMALIZE_EMBEDDINGS
        
        logger.info(f"Loading embedding model: {self.model_name} on device={self.device}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        self.dim = int(self.model.get_sentence_embedding_dimension())
        logger.info(f"Loaded embedding model: {self.model_name} ({self.dim} dims)")

    def _encode(self, texts: List[str] | str, normalize: bool | None = None) -> np.ndarray:
        norm = self.normalize if normalize is None else normalize
        input_texts = [texts] if isinstance(texts, str) else texts
        
        embeddings = self.model.encode(
            input_texts,
            normalize_embeddings=bool(norm),
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        return embeddings

    async def embed_text(self, text: str) -> np.ndarray:
        return self._encode(text)[0]

    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)
        return self._encode(texts)

    def embedding_dimension(self) -> int:
        return self.dim

embedding_service = EmbeddingService()