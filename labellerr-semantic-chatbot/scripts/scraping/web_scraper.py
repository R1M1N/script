#!/usr/bin/env python3
"""
Web Scraper for Labellerr Content
Scrapes all specified Labellerr pages and extracts clean text content.
"""

import os
import sys
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from config.settings import LABELLERR_PAGES, REQUEST_TIMEOUT, MAX_REQUESTS_PER_SECOND

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LabellerrWebScraper:
    def __init__(self, output_dir="../../data_ingest/raw"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def fetch_page(self, url):
        """Fetch a single page and return BeautifulSoup object"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def extract_text_chunks(self, text, max_words=300):
        """Split text into chunks for better embedding"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i:i + max_words])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk.strip())
        return chunks
    
    def clean_text(self, soup):
        """Extract and clean visible text from soup"""
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Get text and clean it
        text = soup.get_text(separator=" ", strip=True)
        
        # Remove extra whitespace and normalize
        text = " ".join(text.split())
        return text
    
    def extract_metadata(self, soup, url):
        """Extract page metadata"""
        metadata = {
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "title": "",
            "description": "",
            "keywords": [],
            "page_type": self.get_page_type(url)
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Extract meta description
        desc_tag = soup.find('meta', {'name': 'description'})
        if desc_tag:
            metadata["description"] = desc_tag.get('content', '').strip()
        
        # Extract keywords
        keywords_tag = soup.find('meta', {'name': 'keywords'})
        if keywords_tag:
            keywords = keywords_tag.get('content', '')
            metadata["keywords"] = [k.strip() for k in keywords.split(',') if k.strip()]
        
        # Extract Open Graph data
        og_title = soup.find('meta', {'property': 'og:title'})
        if og_title and not metadata["title"]:
            metadata["title"] = og_title.get('content', '').strip()
        
        og_desc = soup.find('meta', {'property': 'og:description'})
        if og_desc and not metadata["description"]:
            metadata["description"] = og_desc.get('content', '').strip()
        
        return metadata
    
    def get_page_type(self, url):
        """Determine page type based on URL"""
        url_lower = url.lower()
        if 'blog' in url_lower:
            return 'blog'
        elif 'case-studies' in url_lower:
            return 'case_study'
        elif 'docs' in url_lower:
            return 'documentation'
        elif 'faq' in url_lower:
            return 'faq'
        elif 'pricing' in url_lower:
            return 'pricing'
        elif any(term in url_lower for term in ['demo', 'interactive']):
            return 'demo'
        elif any(term in url_lower for term in ['platform', 'annotation', 'tool']):
            return 'product'
        elif any(term in url_lower for term in ['automotive', 'healthcare', 'retail', 'energy']):
            return 'solution'
        else:
            return 'general'
    
    def scrape_page(self, url):
        """Scrape a single page and return structured data"""
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        # Extract metadata
        metadata = self.extract_metadata(soup, url)
        
        # Extract and clean text
        clean_text = self.clean_text(soup)
        
        # Create chunks
        chunks = self.extract_text_chunks(clean_text)
        
        return {
            "source_type": "webpage",
            "metadata": metadata,
            "full_text": clean_text,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
    
    def scrape_all_pages(self):
        """Scrape all configured Labellerr pages"""
        results = []
        failed_urls = []
        
        logger.info(f"Starting to scrape {len(LABELLERR_PAGES)} pages...")
        
        for i, url in enumerate(LABELLERR_PAGES, 1):
            try:
                logger.info(f"[{i}/{len(LABELLERR_PAGES)}] Processing: {url}")
                
                page_data = self.scrape_page(url)
                if page_data:
                    results.append(page_data)
                    logger.info(f"✅ Successfully scraped: {page_data['metadata']['title']}")
                else:
                    failed_urls.append(url)
                    logger.warning(f"❌ Failed to scrape: {url}")
                
                # Rate limiting
                if i < len(LABELLERR_PAGES):
                    time.sleep(1 / MAX_REQUESTS_PER_SECOND)
                    
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                failed_urls.append(url)
        
        # Save results
        output_file = os.path.join(self.output_dir, "labellerr_content.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Save summary
        summary = {
            "total_pages": len(LABELLERR_PAGES),
            "successful_scrapes": len(results),
            "failed_scrapes": len(failed_urls),
            "failed_urls": failed_urls,
            "total_chunks": sum(item['chunk_count'] for item in results),
            "scrape_completed_at": datetime.now().isoformat()
        }
        
        summary_file = os.path.join(self.output_dir, "scraping_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Scraping complete!")
        logger.info(f"📊 Results: {len(results)} successful, {len(failed_urls)} failed")
        logger.info(f"📁 Saved to: {output_file}")
        logger.info(f"📈 Total chunks created: {summary['total_chunks']}")
        
        return results, summary

def main():
    """Main execution function"""
    scraper = LabellerrWebScraper()
    results, summary = scraper.scrape_all_pages()
    
    print(f"\n🎉 Web scraping completed!")
    print(f"📊 Successfully scraped: {summary['successful_scrapes']} pages")
    print(f"📝 Total text chunks: {summary['total_chunks']}")
    print(f"📁 Output saved to: data_ingest/raw/")

if __name__ == "__main__":
    main()