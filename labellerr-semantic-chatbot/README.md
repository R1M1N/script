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
