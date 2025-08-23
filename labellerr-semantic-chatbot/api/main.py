# Updated api/main.py with search and RAG endpoints
import logging
import time
import uuid
from typing import List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from api.models.schemas import ChatRequest, ChatResponse, SearchResultItem
from api.embedding_service import embedding_service
from api.qdrant_service import qdrant_service
from api.llm_service import llm_service
from api.query_parser import parse_temporal_query, extract_keywords

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
async def health():
    try:
        dim = embedding_service.embedding_dimension()
        count = await qdrant_service.count()
    except Exception:
        dim = None
        count = 0
    
    return {
        "status": "ok",
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "embedding_dimension": dim,
        "vector_db": {
            "chroma_collection": settings.CHROMA_COLLECTION,
            "qdrant_collection": settings.QDRANT_COLLECTION,
            "qdrant_points": count
        }
    }

@app.get("/search", response_model=List[SearchResultItem])
async def search_endpoint(
    q: str = Query(..., description="Search query"),
    k: int = Query(8, ge=1, le=20, description="Number of results")
):
    """Search-only endpoint for debugging retrieval"""
    try:
        # Parse query for filters
        temporal_info = parse_temporal_query(q)
        keywords = extract_keywords(q)
        
        # Embed query
        query_embedding = await embedding_service.embed_text(q)
        
        # Search with filters
        results = await qdrant_service.search(
            query_embedding=query_embedding,
            top_k=k,
            month=temporal_info.get("month"),
            keywords=keywords if keywords else None
        )
        
        # If no results with filters, try without filters
        if not results:
            logger.info("No results with filters, trying without filters...")
            results = await qdrant_service.search(query_embedding=query_embedding, top_k=k)
        
        logger.info(f"Search '{q}' returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.exception(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

def _trim(text: str, max_chars: int) -> str:
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars-3] + "..."

def _build_prompt(question: str, contexts: List[SearchResultItem]) -> tuple[str, str]:
    blocks = []
    for i, c in enumerate(contexts, start=1):
        title = c.title or c.url or c.source_file or f"Snippet {i}"
        snippet = _trim(c.content, settings.RAG_MAX_CONTEXT_CHARS)
        src_line = f"Source {i}: {title}"
        if c.url:
            src_line += f" ({c.url})"
        blocks.append(f"{src_line}\n{snippet}".strip())
    
    context_text = "\n\n".join(blocks) if blocks else "No external context retrieved."
    
    system = (
        "You are a precise, helpful assistant. Use only the provided sources to answer. "
        "If the answer is not contained in the sources, say you don't know. "
        "Cite the sources used under 'Sources:' at the end."
    )
    
    prompt = (
        f"Context:\n{context_text}\n\n"
        f"User question: {question}\n\n"
        f"Instructions:\n"
        f"- Base the answer strictly on the Context above.\n"
        f"- Be concise and factual.\n"
        f"- Include a 'Sources:' section listing the specific sources used.\n"
        f"Answer:"
    )
    
    return system, prompt

@app.post("/rag", response_model=ChatResponse)
async def rag_endpoint(request: ChatRequest) -> ChatResponse:
    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    logger.info(f"[RAG] qid={conversation_id} | msg='{request.message[:80]}' | k={request.context_k}")
    
    try:
        # Parse query for filters
        temporal_info = parse_temporal_query(request.message)
        keywords = extract_keywords(request.message)
        
        # Embed query
        query_embedding = await embedding_service.embed_text(request.message)
        
        # Smart retrieval with filters
        contexts = await qdrant_service.search(
            query_embedding=query_embedding,
            top_k=request.context_k,
            month=temporal_info.get("month"),
            keywords=keywords if keywords else None
        )
        
        # If no results with filters, try without filters
        if not contexts:
            logger.info("No results with filters, trying without filters...")
            contexts = await qdrant_service.search(
                query_embedding=query_embedding, 
                top_k=request.context_k
            )
        
        # Build prompt and generate
        system_instruction, prompt = _build_prompt(request.message, contexts)
        answer = await llm_service.generate(
            prompt=prompt,
            system_instruction=system_instruction
        )
        
        processing_time = round((time.time() - start_time) * 1000.0, 2)
        
        logger.info(f"[RAG] qid={conversation_id} | retrieved={len(contexts)} | {processing_time}ms")
        
        return ChatResponse(
            response=answer,
            context_used=contexts,
            conversation_id=conversation_id,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.exception(f"[RAG] qid={conversation_id} failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG failed: {e}")

@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "status": "ok"}