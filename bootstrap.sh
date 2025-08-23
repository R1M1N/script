#!/bin/bash
set -euo pipefail

PROJECT=labellerr-semantic-chatbot
PYVER=3.10
ENV=chatbot

# 1) Create project directory (idempotent)
mkdir -p "$PROJECT"
cd "$PROJECT"

# 2) Conda env
if ! conda env list | grep -q "^$ENV "; then
  conda create -n "$ENV" python="$PYVER" -y
fi
# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV"

# 3) Directories
mkdir -p data_ingest/{raw,processed,embeddings}
mkdir -p scripts/{scraping,processing,embedding}
mkdir -p api/{routes,models,utils}
mkdir -p frontend/{components,static,templates}
mkdir -p config docs tests

# 4) Files
touch README.md
touch .env
touch config/__init__.py
touch scripts/scraping/__init__.py
touch scripts/processing/__init__.py
touch scripts/embedding/__init__.py
touch api/routes/__init__.py
touch api/models/__init__.py
touch api/utils/__init__.py
touch tests/__init__.py
touch frontend/components/__init__.py

# 5) .gitignore
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*.pyo
*.egg-info/
.venv/
.env
.env.*
.cache/
.ipynb_checkpoints/

# Data
data_ingest/processed/
data_ingest/embeddings/
qdrant_storage/
chroma/
*.db
*.sqlite

# OS
.DS_Store

# Logs
logs/
*.log
EOF

# 6) requirements.txt (pin core libs you're using)
cat > requirements.txt <<'EOF'
fastapi==0.111.0
uvicorn[standard]==0.30.0
pydantic==2.8.2
pydantic-settings==2.3.4
sentence-transformers==3.0.1
numpy==1.26.4
chromadb==0.5.5
qdrant-client==1.9.2
google-generativeai==0.7.2
python-dotenv==1.0.1
requests==2.32.3
tqdm==4.66.5
EOF

# 7) config/settings.py (env-driven)
cat > config/settings.py <<'EOF'
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "labellerr-semantic-chatbot"
    LOG_LEVEL: str = "INFO"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Embeddings
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    NORMALIZE_EMBEDDINGS: bool = True

    # Vector DB (default to Chroma; you can switch to Qdrant later)
    CHROMA_DIR: str = "./data_ingest/vector_db"
    CHROMA_COLLECTION: str = "labellerr_content_minilm"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "updates_minilm"

    # RAG
    RAG_TOP_K: int = 5
    RAG_MAX_CONTEXT_CHARS: int = 1200

    # Gemini
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
EOF

# 8) .env template
cat > .env <<'EOF'
# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Embeddings
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
NORMALIZE_EMBEDDINGS=true

# Chroma
CHROMA_DIR=./data_ingest/vector_db
CHROMA_COLLECTION=labellerr_content_minilm

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=updates_minilm

# RAG
RAG_TOP_K=5
RAG_MAX_CONTEXT_CHARS=1200

# Gemini
GEMINI_MODEL=gemini-2.5-pro
GOOGLE_API_KEY=
EOF

# 9) Minimal API app with health and RAG stub
cat > api/main.py <<'EOF'
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "vector_db": {
            "chroma_collection": settings.CHROMA_COLLECTION,
            "qdrant_collection": settings.QDRANT_COLLECTION
        }
    }

@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "status": "ok"}
EOF

# 10) Basic schemas
cat > api/models/schemas.py <<'EOF'
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
EOF

# 11) Placeholders for scripts
cat > scripts/processing/chunker.py <<'EOF'
def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150):
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + max_chars, len(text))
        chunk = text[i:end]
        if chunk.strip():
            chunks.append(chunk)
        if end >= len(text):
            break
        i = max(i + 1, end - overlap)
    return chunks
EOF

cat > scripts/embedding/vector_db.py <<'EOF'
# Placeholder: swap between Chroma and Qdrant in future steps.
EOF

# 12) README starter
cat > README.md <<'EOF'
# Labellerr Semantic Chatbot

Quick start:
1) Create/activate env and install deps
   conda activate chatbot
   pip install -r requirements.txt

2) Run API
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

Next steps:
- Implement embedding service and RAG orchestrator
- Choose vector DB (Chroma or Qdrant) and index documents
EOF

# 13) Makefile (handy shortcuts)
cat > Makefile <<'EOF'
.PHONY: install run fmt lint test

install:
	pip install -r requirements.txt

run:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

fmt:
	python -m pip install ruff
	ruff check --select I --fix .
	ruff format .

test:
	pytest -q
EOF

echo "✅ Project scaffold created."
echo "➡ Next:"
echo "1) conda activate $ENV"
echo "2) pip install -r requirements.txt"
echo "3) uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo "4) Open http://localhost:8000/health"
