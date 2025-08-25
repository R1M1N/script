from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid
import numpy as np
from typing import List, Dict, Any, Optional
import json

class QdrantManager:
    def __init__(self, host: str = "localhost", port: int = 6333, api_key: str = None):
        """
        Initialize Qdrant client
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
            api_key: API key for Qdrant Cloud (optional)
        """
        if api_key:
            self.client = QdrantClient(url=f"https://{host}", api_key=api_key)
        else:
            self.client = QdrantClient(host=host, port=port)
        
        self.collection_name = "labellerr_knowledge_base"
        print(f"Connected to Qdrant at {host}:{port}")
    
    def create_collection(self, vector_size: int = 768, distance: Distance = Distance.COSINE):
        """
        Create collection for storing embeddings
        
        Args:
            vector_size: Dimension of embeddings (768 for all-mpnet-base-v2, 384 for all-MiniLM-L6-v2)
            distance: Distance metric for similarity search
        """
        try:
            # Delete collection if exists
            self.client.delete_collection(collection_name=self.collection_name)
            print(f"Deleted existing collection: {self.collection_name}")
        except:
            pass
        
        # Create new collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=distance)
        )
        print(f"Created collection: {self.collection_name} with vector size: {vector_size}")
    
    def store_chunks_with_embeddings(self, chunks: List[Dict], embeddings: np.ndarray):
        """
        Store chunks and their embeddings in Qdrant
        
        Args:
            chunks: List of chunk dictionaries with metadata
            embeddings: Numpy array of embeddings
        """
        points = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    'chunk_id': chunk.get('id', f"chunk_{i}"),
                    'text': chunk.get('text', ''),
                    'title': chunk.get('title', ''),
                    'url': chunk.get('url', ''),
                    'heading': chunk.get('heading', ''),
                    'source_type': chunk.get('source_type', 'unknown'),
                    'chunk_index': chunk.get('chunk_index', 0),
                    'page_title': chunk.get('page_title', ''),
                    'heading_level': chunk.get('heading_level', 0),
                    'embedding_model': chunk.get('embedding_model', ''),
                    'char_count': len(chunk.get('text', '')),
                    'word_count': len(chunk.get('text', '').split())
                }
            )
            points.append(point)
        
        # Upload points in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
            print(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")
        
        print(f"Successfully stored {len(points)} chunks in Qdrant")
    
    def search_similar(self, query_embedding: np.ndarray, limit: int = 5, 
                      source_filter: Optional[str] = None, min_score: float = 0.0):
        """
        Search for similar chunks
        
        Args:
            query_embedding: Query vector
            limit: Number of results to return
            source_filter: Filter by source type (e.g., 'documentation', 'blog', 'youtube')
            min_score: Minimum similarity score
        """
        search_filter = None
        if source_filter:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="source_type",
                        match=MatchValue(value=source_filter)
                    )
                ]
            )
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            query_filter=search_filter,
            limit=limit,
            score_threshold=min_score
        )
        
        return search_result
    
    def get_collection_info(self):
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'status': info.status,
                'vectors_count': info.vectors_count,
                'segments_count': info.segments_count,
                'disk_data_size': info.disk_data_size,
                'ram_data_size': info.ram_data_size
            }
        except Exception as e:
            return {'error': str(e)}
