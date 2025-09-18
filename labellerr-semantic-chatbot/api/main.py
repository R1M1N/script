# Updated api/main.py with proper initialization

import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import time
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

from config.settings import settings
from api.models.schemas import ChatRequest, ChatResponse, SearchResultItem
from api.embedding_service import EmbeddingGenerator
from api.qdrant_service import QdrantManager
from api.llm_service import LabellerrRAGChatbot
from api.query_parser import parse_temporal_query, extract_keywords

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)
app.mount("/app", StaticFiles(directory="frontend", html=True), name="app")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service variables
embedding_service = None
qdrant_service = None
llm_service = None
chatbot = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global embedding_service, qdrant_service, llm_service, chatbot
    
    try:
        logger.info("Initializing services...")
        
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Initialize services
        embedding_service = EmbeddingGenerator(model_name=settings.EMBEDDING_MODEL)
        qdrant_service = QdrantManager(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        
        # Initialize chatbot
        chatbot = LabellerrRAGChatbot(
            qdrant_manager=qdrant_service,
            embedding_generator=embedding_service,
            gemini_api_key=settings.GEMINI_API_KEY,
            model="gemini-2.5-pro" 
        )
        
        logger.info("✅ Services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "embedding_model": settings.EMBEDDING_MODEL,
        "qdrant_host": settings.QDRANT_HOST,
        "debug_mode": settings.DEBUG,
        "services_initialized": chatbot is not None
    }

@app.get("/search", response_model=List[SearchResultItem])
async def search_endpoint(
    q: str = Query(..., description="Search query"),
    k: int = Query(8, ge=1, le=20, description="Number of results")
):
    """Search-only endpoint for debugging retrieval"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        logger.info(f"Search query: '{q}' with k={k}")
        
        # Use chatbot's retrieve_context method
        context = chatbot.retrieve_context(q, k)
        
        # Convert to SearchResultItem format
        results = []
        for ctx in context:
            result = SearchResultItem(
                title=ctx.get('title'),
                url=ctx.get('url'),
                content=ctx.get('text', ''),
                distance=1.0 - ctx.get('score', 0.0),  # Convert similarity to distance
                source_file=ctx.get('source_type'),
                chunk_id=ctx.get('id')
            )
            results.append(result)
        
        logger.info(f"Search '{q}' returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.exception(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

def _trim(text: str, max_chars: int = 1000) -> str:
    """Trim text to max_chars"""
    if not text or len(text) <= max_chars:
        return text
    return text[:max_chars-3] + "..."

@app.post("/rag", response_model=ChatResponse)
async def rag_endpoint(request: ChatRequest) -> ChatResponse:
    """RAG endpoint for chat functionality"""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    start_time = time.time()
    conversation_id = getattr(request, 'conversation_id', None) or str(uuid.uuid4())
    
    logger.info(f"[RAG] qid={conversation_id} | msg='{request.message[:80]}' | k={request.context_k}")
    
    try:
        # Use the chatbot's chat method
        result = chatbot.chat(request.message, top_k=request.context_k)
        
        # Convert context to SearchResultItem format with ACTUAL content
        context_used = []
        for source in result.get('sources', []):
            # Get the actual text from the original context
            actual_text = source.get('text', '')  # This should contain the actual content
            
            item = SearchResultItem(
                title=source.get('title'),
                url=source.get('url'),
                content=actual_text[:1000],  # First 1000 chars of actual content
                distance=1.0 - source.get('score', 0.0),
                source_file=source.get('source_type'),
                chunk_id=source.get('id')
            )
            context_used.append(item)
        
        processing_time = round((time.time() - start_time) * 1000.0, 2)
        
        logger.info(f"[RAG] qid={conversation_id} | retrieved={len(context_used)} | {processing_time}ms")
        
        return ChatResponse(
            response=result['response'],
            context_used=context_used,
            conversation_id=conversation_id,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.exception(f"[RAG] qid={conversation_id} failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME, 
        "status": "ok",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "chat": "/rag",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
