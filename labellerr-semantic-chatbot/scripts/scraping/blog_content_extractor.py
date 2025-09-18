#!/usr/bin/env python3
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

class BlogContentExtractor:
    def __init__(self):
        self.output_dir = "../../data_ingest/raw/blog"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.extracted_posts = []
        self.failed_urls = []

    def extract_blog_metadata(self, soup, url):
        metadata = {
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "title": "",
            "author": "",
            "publish_date": "",
            "tags": [],
        }
        
        # Extract title
        title_elem = soup.select_one('h1')
        if title_elem:
            metadata["title"] = title_elem.get_text(strip=True)
        
        # Extract meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            metadata["meta_description"] = meta_desc.get('content', '').strip()
        
        return metadata

    def clean_blog_content(self, soup):
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            element.decompose()
        
        # Find main content
        content_element = soup.select_one('article') or soup.select_one('main') or soup.find('body')
        
        if content_element:
            text = content_element.get_text(separator='\n', strip=True)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            return text.strip()
        return ""

    def create_content_chunks(self, content, max_words=300):
        if not content:
            return []
        
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            test_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
            word_count = len(test_chunk.split())
            
            if word_count > max_words and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk = test_chunk
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def extract_single_post(self, url):
        try:
            print(f"📖 Extracting: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            metadata = self.extract_blog_metadata(soup, url)
            content = self.clean_blog_content(soup)
            chunks = self.create_content_chunks(content)
            
            post_data = {
                "source_type": "blog_post",
                "metadata": metadata,
                "full_text": content,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "word_count": len(content.split()) if content else 0,
            }
            
            print(f"✅ Extracted: {metadata['title'][:50]}... ({len(chunks)} chunks)")
            return post_data
            
        except Exception as e:
            print(f"❌ Failed to extract {url}: {e}")
            self.failed_urls.append({"url": url, "error": str(e)})
            return None

    def extract_all_blog_content(self):
        # Load the links from Step 1
        links_file = os.path.join(self.output_dir, "playwright_blog_links.json")
        
        if not os.path.exists(links_file):
            print(f"❌ Links file not found: {links_file}")
            print("Run the playwright link extractor first!")
            return
        
        with open(links_file, 'r', encoding='utf-8') as f:
            blog_urls = json.load(f)
        
        print(f"🚀 Starting extraction from {len(blog_urls)} blog posts...")
        
        for i, url in enumerate(blog_urls, 1):
            print(f"\n[{i}/{len(blog_urls)}] Processing: {url}")
            post_data = self.extract_single_post(url)
            if post_data:
                self.extracted_posts.append(post_data)
            time.sleep(1)  # Rate limiting
        
        # Save results
        content_file = os.path.join(self.output_dir, "all_blog_posts_content.json")
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_posts, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 Blog content extraction completed!")
        print(f"📊 Successfully extracted: {len(self.extracted_posts)} posts")
        print(f"📁 Saved to: {content_file}")

def main():
    extractor = BlogContentExtractor()
    extractor.extract_all_blog_content()

if __name__ == "__main__":
    main()
