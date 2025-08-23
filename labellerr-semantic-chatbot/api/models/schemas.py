from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    context_k: int = Field(5, ge=1, le=20)

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
