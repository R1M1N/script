# api/qdrant_service.py
import logging
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, Should, Must
import numpy as np

from config.settings import settings
from api.models.schemas import SearchResultItem

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.QDRANT_COLLECTION
        logger.info(f"Initialized Qdrant client: {self.collection_name}")

    async def search(
        self, 
        query_embedding: np.ndarray | List[float], 
        top_k: int = 8,
        month: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        min_score: float = 0.0
    ) -> List[SearchResultItem]:
        
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()
        
        # Build filters
        query_filter = None
        if month or keywords:
            must_conditions = []
            should_conditions = []
            
            if month:
                must_conditions.append(FieldCondition(key="month", match=MatchValue(value=month)))
            
            if keywords:
                for keyword in keywords:
                    should_conditions.extend([
                        FieldCondition(key="title", match=MatchValue(value=keyword)),
                        FieldCondition(key="tags", match=MatchValue(value=keyword))
                    ])
            
            if must_conditions or should_conditions:
                query_filter = Filter(
                    must=must_conditions if must_conditions else None,
                    should=should_conditions if should_conditions else None
                )
        
        try:
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
                score_threshold=min_score
            )
            
            # Convert to SearchResultItem
            items = []
            for hit in results:
                payload = hit.payload or {}
                items.append(SearchResultItem(
                    title=payload.get("title"),
                    url=payload.get("url"),
                    content=payload.get("text", ""),
                    distance=1.0 - hit.score,  # Convert similarity to distance
                    source_file=payload.get("source_file"),
                    chunk_id=str(payload.get("chunk_id", ""))
                ))
            
            return items
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    async def count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception:
            return 0

qdrant_service = QdrantService()