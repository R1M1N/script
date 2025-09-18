import json
import numpy as np
import os
from sentence_transformers import SentenceTransformer

def generate_embeddings():
    # Load processed chunks
    with open("processed_chunks_ready_for_qdrant.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Initialize embedding model
    model = SentenceTransformer("all-mpnet-base-v2")
    print(f"Model loaded: {model}")
    
    # Extract texts for embedding
    texts = [chunk["text"] for chunk in chunks]
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    
    # Create output directory
    os.makedirs("../../embeddings_output", exist_ok=True)
    
    # Save embeddings and chunks
    np.save("../../embeddings_output/embeddings.npy", embeddings)
    
    with open("../../embeddings_output/chunks_with_metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    # Save metadata
    metadata = {
        "total_chunks": len(chunks),
        "embedding_model": "all-mpnet-base-v2", 
        "embedding_dimension": embeddings.shape[1],
        "source_distribution": {}
    }
    
    for chunk in chunks:
        source = chunk.get("source_type", "unknown")
        metadata["source_distribution"][source] = metadata["source_distribution"].get(source, 0) + 1
    
    with open("../../embeddings_output/embedding_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Saved {len(embeddings)} embeddings to embeddings_output/")
    print(f"Embedding shape: {embeddings.shape}")
    print(f"Metadata: {metadata}")

if __name__ == "__main__":
    generate_embeddings()
