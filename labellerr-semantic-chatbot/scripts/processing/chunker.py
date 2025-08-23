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
