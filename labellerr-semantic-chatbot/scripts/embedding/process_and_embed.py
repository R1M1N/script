import re
import json
import hashlib
from typing import List, Dict, Any
from bs4 import BeautifulSoup

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove navigation/footer/header
        text = re.sub(r'(Navigation|Footer|Header).*?(?=\n|$)', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def chunk_text(self, text: str, url: str, title: str, source_type: str = "doc", heading: str = "") -> List[Dict]:
        if not text.strip():
            return []
            
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            # Create unique chunk ID
            chunk_id = hashlib.md5(f"{url}_{heading}_{i}_{source_type}".encode()).hexdigest()
            
            chunks.append({
                'id': chunk_id,
                'text': chunk_text,
                'url': url,
                'title': title,
                'heading': heading,
                'chunk_index': i // (self.chunk_size - self.chunk_overlap),
                'source_type': source_type
            })
        
        return chunks

    def load_json(self, filepath: str) -> Any:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def process_structured_documentation_json(self, filepath: str) -> List[Dict]:
        """
        Process your specific JSON structure:
        [
          {
            "heading": "...",
            "level": 2,
            "content": "...",
            "chunks": [],
            "url": "...",
            "page_title": "..."
          }
        ]
        """
        data = self.load_json(filepath)
        all_chunks = []
        
        for entry in data:
            if isinstance(entry, dict):
                # Extract fields
                heading = entry.get('heading', '')
                content = entry.get('content', '')
                url = entry.get('url', '')
                page_title = entry.get('page_title', heading)
                level = entry.get('level', 1)
                
                # Skip entries with no content
                if not content.strip():
                    continue
                
                # Clean the content
                cleaned_content = self.clean_text(content)
                
                # Create a combined title for better context
                if heading and page_title and heading != page_title:
                    combined_title = f"{page_title} - {heading}"
                else:
                    combined_title = page_title or heading
                
                # Generate chunks
                chunks = self.chunk_text(
                    text=cleaned_content,
                    url=url,
                    title=combined_title,
                    source_type="documentation",
                    heading=heading
                )
                
                # Add additional metadata to chunks
                for chunk in chunks:
                    chunk.update({
                        'heading_level': level,
                        'page_title': page_title,
                        'original_heading': heading
                    })
                
                all_chunks.extend(chunks)
        
        return all_chunks
    
    def process_website_content_json(self, filepath: str) -> List[Dict]:
        """
        Accepts flexible shapes like:
        1) [{"url": "...", "title": "...", "text"/"content"/"html": "...", "sections": [{"heading": "...", "text"/"html": "..."}]}]
        2) {"pages": [ ...same as above... ]}
        3) Any entry may carry "page_title", "level"
        """
        data = self.load_json(filepath)
        pages = data.get("pages") if isinstance(data, dict) else data
        if not isinstance(pages, list):
            return []

        all_chunks = []

        def extract_text(maybe_html_or_text: str) -> str:
            if not maybe_html_or_text:
                return ""
            # If HTML-like, strip tags
            if "<" in maybe_html_or_text and ">" in maybe_html_or_text:
                soup = BeautifulSoup(maybe_html_or_text, "html.parser")
                return self.clean_text(soup.get_text(separator=" ", strip=True))
            return self.clean_text(maybe_html_or_text)

        for entry in pages:
            if not isinstance(entry, dict):
                continue

            url = entry.get("url", "")
            page_title = entry.get("page_title", entry.get("title", "")) or ""
            level = int(entry.get("level", 2))

            # Whole-page content
            raw_body = (
                entry.get("text")
                or entry.get("content")
                or entry.get("body")
                or entry.get("markdown")
                or entry.get("html")
                or ""
            )
            body = extract_text(raw_body)

            # Sectioned content
            sections = entry.get("sections") if isinstance(entry.get("sections"), list) else []

            # If sections exist, chunk per section; else chunk the whole page
            if sections:
                for sec in sections:
                    if not isinstance(sec, dict):
                        continue
                    heading = sec.get("heading", "") or sec.get("title", "")
                    raw_sec_text = sec.get("text") or sec.get("content") or sec.get("html") or ""
                    sec_text = extract_text(raw_sec_text)
                    if not sec_text.strip():
                        continue

                    chunks = self.chunk_text(
                        text=sec_text,
                        url=url,
                        title=f"{page_title} - {heading}" if page_title and heading and page_title != heading else (page_title or heading),
                        source_type="website",
                        heading=heading
                    )
                    for c in chunks:
                        c.update({
                            "heading_level": int(sec.get("level", level)),
                            "page_title": page_title,
                            "original_heading": heading
                        })
                    all_chunks.extend(chunks)
            else:
                if body.strip():
                    chunks = self.chunk_text(
                        text=body,
                        url=url,
                        title=page_title or (url or "Website Page"),
                        source_type="website",
                        heading=""
                    )
                    for c in chunks:
                        c.update({
                            "heading_level": level,
                            "page_title": page_title,
                            "original_heading": ""
                        })
                    all_chunks.extend(chunks)

        return all_chunks


    def process_blog_json_structured(self, filepath: str) -> List[Dict]:
        """
        Process blog JSON with similar structure or different structure
        """
        data = self.load_json(filepath)
        all_chunks = []
        
        # Handle if it's a list of blog posts
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    content = entry.get('content', entry.get('body', entry.get('text', '')))
                    title = entry.get('title', entry.get('heading', ''))
                    url = entry.get('url', entry.get('link', ''))
                    
                    if content.strip():
                        cleaned_content = self.clean_text(content)
                        chunks = self.chunk_text(
                            text=cleaned_content,
                            url=url,
                            title=title,
                            source_type="blog"
                        )
                        all_chunks.extend(chunks)
        
        return all_chunks

    def process_youtube_transcripts_structured(self, filepath: str) -> List[Dict]:
        """
        Process YouTube transcripts JSON
        """
        data = self.load_json(filepath)
        all_chunks = []
        
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    transcript = entry.get('transcript', entry.get('content', entry.get('text', '')))
                    title = entry.get('title', '')
                    url = entry.get('url', entry.get('video_url', ''))
                    duration = entry.get('duration', '')
                    
                    if transcript.strip():
                        cleaned_transcript = self.clean_text(transcript)
                        chunks = self.chunk_text(
                            text=cleaned_transcript,
                            url=url,
                            title=f"Video: {title}",
                            source_type="youtube"
                        )
                        
                        # Add video metadata
                        for chunk in chunks:
                            chunk.update({
                                'video_duration': duration,
                                'video_title': title
                            })
                        
                        all_chunks.extend(chunks)
        
        return all_chunks

    def process_txt(self, filepath: str, default_url: str = '', default_title: str = '') -> List[Dict]:
        """Process plain text files"""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        cleaned_text = self.clean_text(text)
        url = default_url or filepath
        title = default_title or f"Text File: {filepath}"
        
        return self.chunk_text(
            text=cleaned_text,
            url=url,
            title=title,
            source_type="text"
        )

    def process_html(self, filepath: str, default_url: str = '', default_title: str = '') -> List[Dict]:
        """Process HTML files"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text(separator=' ', strip=True)
        cleaned_text = self.clean_text(text)
        
        url = default_url or filepath
        title = default_title or f"HTML File: {filepath}"
        
        return self.chunk_text(
            text=cleaned_text,
            url=url,
            title=title,
            source_type="html"
        )

    def process_all_files(self, file_config: Dict[str, str]) -> List[Dict]:
        all_chunks = []
        for filepath, file_type in file_config.items():
            print(f"Processing {filepath} as {file_type}...")
            try:
                if file_type == "structured_documentation":
                    chunks = self.process_structured_documentation_json(filepath)
                elif file_type == "blog_json":
                    chunks = self.process_blog_json_structured(filepath)
                elif file_type == "youtube_json":
                    chunks = self.process_youtube_transcripts_structured(filepath)
                elif file_type == "txt":
                    chunks = self.process_txt(filepath, filepath, f"Text File: {filepath}")
                elif file_type == "html":
                    chunks = self.process_html(filepath, filepath, f"HTML File: {filepath}")
                elif file_type == "website_content":
                    chunks = self.process_website_content_json(filepath)  # NEW
                else:
                    print(f"Unknown file type: {file_type} for {filepath}")
                    continue

                all_chunks.extend(chunks)
                print(f"  -> Generated {len(chunks)} chunks from {filepath}")
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                continue
        return all_chunks

        
        

    def save_chunks(self, chunks: List[Dict], output_file: str = "processed_chunks.json"):
        """Save processed chunks to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(chunks)} chunks to {output_file}")

    def get_summary_stats(self, chunks: List[Dict]) -> Dict:
        """Get summary statistics of processed chunks"""
        if not chunks:
            return {"total_chunks": 0}
        
        stats = {
            "total_chunks": len(chunks),
            "source_types": {},
            "avg_chunk_length": sum(len(chunk['text']) for chunk in chunks) / len(chunks),
            "urls_count": len(set(chunk['url'] for chunk in chunks)),
            "sample_chunk": chunks[0] if chunks else None
        }
        
        # Count by source type
        for chunk in chunks:
            source_type = chunk.get('source_type', 'unknown')
            stats['source_types'][source_type] = stats['source_types'].get(source_type, 0) + 1
        
        return stats

# Usage Example:
if __name__ == "__main__":
    processor = DocumentProcessor(chunk_size=800, chunk_overlap=100)
    
    # Define your files with the correct types based on your structure
    files_to_process = {
        'data/labellerr_documentation_complete.json': 'structured_documentation',
        'data/documentation_complete_with_selenium.json': 'structured_documentation', 
        'data/labellerr_docs_structured.json': 'structured_documentation',
        'data/all_blog_posts_content.json': 'blog_json',
        'data/youtube_videos_with_transcripts.json': 'youtube_json',
        'data/all_documentation_text.txt': 'txt',
        'data/docs_html_content.html': 'html',
        'data/website_content_extracted.json': 'website_content'
    }
    
    # Process all files
    all_chunks = processor.process_all_files(files_to_process)
    
    # Get statistics
    stats = processor.get_summary_stats(all_chunks)
    print(f"\n=== Processing Summary ===")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Average chunk length: {stats['avg_chunk_length']:.1f} characters")
    print(f"Unique URLs: {stats['urls_count']}")
    print(f"Source distribution: {stats['source_types']}")
    
    # Save processed chunks
    processor.save_chunks(all_chunks, "processed_chunks_ready_for_qdrant.json")
    
    # Show sample chunk structure
    if all_chunks:
        print(f"\n=== Sample Chunk ===")
        sample = all_chunks[0]
        for key, value in sample.items():
            if key == 'text':
                print(f"{key}: {str(value)[:100]}...")
            else:
                print(f"{key}: {value}")
