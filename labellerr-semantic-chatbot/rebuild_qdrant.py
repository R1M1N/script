#!/usr/bin/env python3
"""
Smart Qdrant indexer that filters for update-related content and chunks intelligently
"""
import os
import json
import glob
import uuid
import re
from datetime import datetime
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Configuration
RAW_DIR = os.path.abspath("data_ingest/raw")
MODEL = "all-MiniLM-L6-v2"
COLLECTION = "updates_minilm"
CHUNK_SIZE = 1200  # characters
OVERLAP = 150

def parse_date(date_str):
    """Extract month from date string like '2025-05-15' or 'May 2025'"""
    if not date_str:
        return None
    try:
        # Try ISO format first
        if re.match(r'\d{4}-\d{2}-\d{2}', str(date_str)):
            return str(date_str)[:7]  # 2025-05
        # Try month year format
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        for month, num in months.items():
            if month in str(date_str).lower():
                year_match = re.search(r'20\d{2}', str(date_str))
                if year_match:
                    return f"{year_match.group()}-{num}"
    except:
        pass
    return None

def extract_tags(record):
    """Extract tags that indicate product updates"""
    tags = []
    title = (record.get("title") or "").lower()
    url = (record.get("url") or "").lower()
    categories = record.get("categories", [])
    
    # Check for update-related keywords
    update_keywords = ["product", "update", "release", "changelog", "whats-new", "announcement"]
    for keyword in update_keywords:
        if keyword in title or keyword in url:
            tags.append(keyword)
    
    # Add categories if they exist
    if isinstance(categories, list):
        tags.extend([cat.lower() for cat in categories if isinstance(cat, str)])
    
    return list(set(tags))  # Remove duplicates

def should_include(record):
    """Filter for update-related content"""
    title = (record.get("title") or "").lower()
    url = (record.get("url") or "").lower()
    
    # Must contain update-related keywords
    update_terms = ["product", "update", "release", "changelog", "whats-new", "announcement", "2025"]
    return any(term in title or term in url for term in update_terms)

def chunk_text(text, max_chars=1200, overlap=150):
    """Split text into overlapping chunks"""
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + max_chars, len(text))
        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind('.', i, end)
            if last_period > i + max_chars * 0.7:
                end = last_period + 1
        
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        
        if end >= len(text):
            break
        i = max(i + 1, end - overlap)
    
    return chunks

def load_documents():
    """Load and process JSON documents"""
    documents = []
    
    for filepath in glob.glob(os.path.join(RAW_DIR, "**/*.json"), recursive=True):
        # Skip system files
        if any(skip in os.path.basename(filepath).lower() 
               for skip in ["_links", "summary", "_raw", "failed", "discovered"]):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue
            
        records = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
        
        for i, record in enumerate(records):
            if not isinstance(record, dict) or not should_include(record):
                continue
                
            # Extract content
            text = ""
            for field in ["content", "full_text", "transcript", "text", "body"]:
                if record.get(field) and len(str(record[field]).strip()) > 100:
                    text = str(record[field])
                    break
            
            if not text or len(text) < 200:
                continue
            
            # Extract metadata
            title = record.get("title") or record.get("heading") or os.path.basename(filepath)
            url = record.get("url", "")
            published_date = record.get("published_date") or record.get("date") or record.get("created_at")
            month = parse_date(published_date)
            tags = extract_tags(record)
            
            # Create chunks
            chunks = chunk_text(text)
            parent_id = record.get("id") or f"{os.path.basename(filepath)}_{i}"
            
            for chunk_idx, chunk_text in enumerate(chunks):
                documents.append({
                    "text": chunk_text,
                    "metadata": {
                        "title": title,
                        "url": url,
                        "published_date": published_date or "",
                        "month": month or "",
                        "tags": tags,
                        "parent_id": parent_id,
                        "chunk_id": chunk_idx,
                        "source_file": os.path.basename(filepath)
                    }
                })
    
    return documents

def main():
    print("🚀 Rebuilding Qdrant with smart filtering and chunking...")
    
    # Initialize Qdrant
    client = QdrantClient(host="localhost", port=6333)
    
    # Recreate collection
    try:
        client.delete_collection(COLLECTION)
        print(f"🗑️  Deleted existing collection: {COLLECTION}")
    except:
        pass
    
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print(f"✅ Created collection: {COLLECTION}")
    
    # Load documents
    documents = load_documents()
    print(f"📊 Loaded {len(documents)} chunks from update-related content")
    
    if not documents:
        print("❌ No documents found!")
        return
    
    # Initialize embedding model
    print("🔄 Loading embedding model...")
    model = SentenceTransformer(MODEL)
    
    # Process in batches
    batch_size = 100
    points = []
    
    for i, doc in enumerate(documents):
        if i % 50 == 0:
            print(f"⚙️  Processing {i}/{len(documents)}...")
        
        # Generate embedding
        embedding = model.encode(doc["text"], normalize_embeddings=True)
        
        # Create point
        point = PointStruct(
            id=i,
            vector=embedding.tolist(),
            payload={**doc["metadata"], "text": doc["text"]}
        )
        points.append(point)
        
        # Upsert batch
        if len(points) >= batch_size:
            client.upsert(collection_name=COLLECTION, points=points)
            points = []
    
    # Upsert remaining
    if points:
        client.upsert(collection_name=COLLECTION, points=points)
    
    print(f"✅ Indexed {len(documents)} chunks")
    
    # Test search
    print("\n🔍 Testing retrieval...")
    test_query = "product update may 2025"
    query_vector = model.encode(test_query, normalize_embeddings=True)
    
    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector.tolist(),
        limit=5,
        with_payload=True
    )
    
    print(f"Top results for '{test_query}':")
    for hit in results:
        payload = hit.payload
        print(f"  - {payload.get('title', 'Untitled')} (month: {payload.get('month', 'N/A')}) [score: {hit.score:.3f}]")
    
    print(f"\n🎉 Qdrant rebuild completed! Collection: {COLLECTION}")

if __name__ == "__main__":
    main()