# Placeholder: swap between Chroma and Qdrant in future steps.
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
import pickle
import os
from tqdm import tqdm
import torch

class EmbeddingGenerator:
    def __init__(self, model_name: str = "all-mpnet-base-v2", device: str = None):
        """
        Initialize embedding generator
        
        Args:
            model_name: Name of the sentence transformer model
                       Options:
                       - "all-mpnet-base-v2" (best quality, 768 dims)
                       - "all-MiniLM-L6-v2" (good speed/quality balance, 384 dims)
                       - "all-MiniLM-L12-v2" (better quality, 384 dims)
            device: Device to run on ('cuda', 'cpu', or None for auto-detect)
        """
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        print(f"Loading model: {model_name} on device: {device}")
        self.model = SentenceTransformer(model_name, device=device)
        self.model_name = model_name
        self.device = device
        
        # Model dimensions
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def prepare_texts_from_chunks(self, chunks: List[Dict]) -> List[str]:
        """
        Extract texts from processed chunks for embedding
        
        Args:
            chunks: List of chunk dictionaries from DocumentProcessor
            
        Returns:
            List of texts ready for embedding
        """
        texts = []
        for chunk in chunks:
            # Create enhanced text for better retrieval
            text = chunk.get('text', '')
            title = chunk.get('title', '')
            heading = chunk.get('heading', '')
            
            # Combine title, heading, and content for richer context
            enhanced_text = ""
            if title:
                enhanced_text += f"Title: {title}\n"
            if heading and heading != title:
                enhanced_text += f"Section: {heading}\n"
            enhanced_text += f"Content: {text}"
            
            texts.append(enhanced_text)
        
        return texts
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a list of texts in batches
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        print(f"Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        print(f"Generated embeddings shape: {embeddings.shape}")
        return embeddings
    
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        embedding = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True)
        return embedding[0]
    
    def process_chunks_to_embeddings(self, chunks: List[Dict], batch_size: int = 32) -> Tuple[List[Dict], np.ndarray]:
        """
        Process chunks and generate embeddings
        
        Args:
            chunks: List of processed chunks
            batch_size: Batch size for embedding generation
            
        Returns:
            Tuple of (chunks_with_metadata, embeddings_array)
        """
        # Prepare texts for embedding
        texts = self.prepare_texts_from_chunks(chunks)
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(texts, batch_size)
        
        # Add embedding metadata to chunks
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            enhanced_chunk = chunk.copy()
            enhanced_chunk['embedding_model'] = self.model_name
            enhanced_chunk['embedding_dim'] = self.embedding_dim
            enhanced_chunk['text_for_embedding'] = texts[i]
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks, embeddings
    
    def save_embeddings_and_chunks(self, chunks: List[Dict], embeddings: np.ndarray, 
                                 output_dir: str = "embeddings_output"):
        """
        Save chunks and embeddings to files
        
        Args:
            chunks: Enhanced chunks with metadata
            embeddings: Embedding vectors
            output_dir: Directory to save files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save chunks as JSON
        chunks_file = os.path.join(output_dir, "chunks_with_metadata.json")
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"Saved chunks to: {chunks_file}")
        
        # Save embeddings as numpy file
        embeddings_file = os.path.join(output_dir, "embeddings.npy")
        np.save(embeddings_file, embeddings)
        print(f"Saved embeddings to: {embeddings_file}")
        
        # Save embedding metadata
        metadata = {
            'model_name': self.model_name,
            'embedding_dim': self.embedding_dim,
            'num_chunks': len(chunks),
            'embedding_shape': embeddings.shape
        }
        
        metadata_file = os.path.join(output_dir, "embedding_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Saved metadata to: {metadata_file}")
    
    def load_embeddings_and_chunks(self, input_dir: str = "embeddings_output") -> Tuple[List[Dict], np.ndarray]:
        """
        Load previously saved chunks and embeddings
        
        Args:
            input_dir: Directory containing saved files
            
        Returns:
            Tuple of (chunks, embeddings)
        """
        chunks_file = os.path.join(input_dir, "chunks_with_metadata.json")
        embeddings_file = os.path.join(input_dir, "embeddings.npy")
        
        # Load chunks
        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        # Load embeddings
        embeddings = np.load(embeddings_file)
        
        print(f"Loaded {len(chunks)} chunks and embeddings with shape {embeddings.shape}")
        return chunks, embeddings
    
    def find_similar_texts(self, query: str, chunks: List[Dict], embeddings: np.ndarray, 
                          top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Find most similar chunks to a query
        
        Args:
            query: Search query
            chunks: List of chunk dictionaries
            embeddings: Embedding vectors
            top_k: Number of top results to return
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = self.generate_single_embedding(query)
        
        # Calculate cosine similarities
        similarities = np.dot(embeddings, query_embedding)
        
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return results with scores
        results = []
        for idx in top_indices:
            results.append((chunks[idx], float(similarities[idx])))
        
        return results

# Usage Example
def main():
    # Initialize embedding generator
    embedder = EmbeddingGenerator(model_name="all-mpnet-base-v2")  # or "all-MiniLM-L6-v2" for speed
    
    # Load processed chunks
    print("Loading processed chunks...")
    with open('api/processed_chunks_ready_for_qdrant.json', 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Generate embeddings
    enhanced_chunks, embeddings = embedder.process_chunks_to_embeddings(chunks, batch_size=32)
    
    # Save embeddings and chunks
    embedder.save_embeddings_and_chunks(enhanced_chunks, embeddings)
    
    # Test similarity search
    print("\n=== Testing Similarity Search ===")
    query = "How to create a new project in Labellerr?"
    similar_chunks = embedder.find_similar_texts(query, enhanced_chunks, embeddings, top_k=3)
    
    print(f"Query: {query}")
    for i, (chunk, score) in enumerate(similar_chunks, 1):
        print(f"\n{i}. Similarity: {score:.3f}")
        print(f"   Title: {chunk['title']}")
        print(f"   Text: {chunk['text'][:150]}...")

if __name__ == "__main__":
    main()
