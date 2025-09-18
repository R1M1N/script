# api/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    context_k: int = 5
    conversation_id: Optional[str] = None

class SearchResultItem(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    content: str
    distance: Optional[float] = None
    source_file: Optional[str] = None
    chunk_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    context_used: List[SearchResultItem] = []
    conversation_id: Optional[str] = None
    processing_time_ms: Optional[float] = None
