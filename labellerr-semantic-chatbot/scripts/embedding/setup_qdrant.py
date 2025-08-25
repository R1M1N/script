# scripts/embedding/setup_qdrant.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api.qdrant_service import QdrantManager
from api.embedding_service import EmbeddingGenerator

def setup_qdrant():
    """Setup Qdrant with processed embeddings"""
    
    # Load embeddings
    embedder = EmbeddingGenerator()
    chunks, embeddings = embedder.load_embeddings_and_chunks("../../embeddings_output/")
    
    # Setup Qdrant
    qdrant_manager = QdrantManager(host="localhost", port=6333)
    qdrant_manager.create_collection(vector_size=embeddings.shape[1])
    qdrant_manager.store_chunks_with_embeddings(chunks, embeddings)
    
    print("✅ Qdrant setup complete!")

if __name__ == "__main__":
    setup_qdrant()
