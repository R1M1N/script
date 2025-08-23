import json
from urllib.parse import urlparse, urlunparse

def normalize_url(url):
    """
    Normalize URL by removing trailing slash and converting to lowercase
    """
    parsed = urlparse(url.lower())
    
    # Remove trailing slash from path (except for root path)
    path = parsed.path.rstrip('/')
    if not path:
        path = '/'
    
    # Reconstruct normalized URL
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))
    
    return normalized

def deduplicate_links(links_data):
    """
    Remove duplicate URLs from the links data structure
    """
    # Track normalized URLs to original URLs
    url_mapping = {}
    unique_urls = []
    
    # Process all_links
    for url in links_data['all_links']:
        normalized = normalize_url(url)
        if normalized not in url_mapping:
            url_mapping[normalized] = url
            unique_urls.append(url)
    
    # Update all_links
    links_data['all_links'] = unique_urls
    links_data['total_links'] = len(unique_urls)
    
    # Update categorized links
    for category in ['internal', 'external', 'social']:
        if category in links_data['categorized']:
            category_urls = []
            category_mapping = {}
            
            for url in links_data['categorized'][category]:
                normalized = normalize_url(url)
                if normalized not in category_mapping:
                    category_mapping[normalized] = url
                    category_urls.append(url)
            
            links_data['categorized'][category] = category_urls
    
    return links_data

def main():
    # Load your existing JSON file
    input_file = "data_ingest/raw/labellerr_homepage_links.json"
    output_file = "data_ingest/raw/labellerr_homepage_links_deduplicated.json"
    
    # Read the JSON data
    with open(input_file, 'r', encoding='utf-8') as f:
        links_data = json.load(f)
    
    print(f"📊 Original links: {links_data['total_links']}")
    
    # Show examples of duplicates before deduplication
    print("\n🔍 Examples of potential duplicates:")
    examples = [
        ("https://www.labellerr.com/blog", "https://www.labellerr.com/blog/"),
        ("https://docs.labellerr.com", "https://docs.labellerr.com/"),
        ("https://www.labellerr.com/", "https://www.labellerr.com")
    ]
    
    for url1, url2 in examples:
        if url1 in links_data['all_links'] and url2 in links_data['all_links']:
            print(f"   • {url1}")
            print(f"   • {url2}")
            print(f"     → Normalized to: {normalize_url(url1)}")
            print()
    
    # Deduplicate
    deduplicated_data = deduplicate_links(links_data.copy())
    
    print(f"✅ Deduplicated links: {deduplicated_data['total_links']}")
    print(f"🗑️  Removed: {links_data['total_links'] - deduplicated_data['total_links']} duplicates")
    
    # Add metadata about deduplication
    deduplicated_data['deduplication_timestamp'] = "2025-08-20T13:27:00"
    deduplicated_data['deduplication_method'] = "URL normalization (lowercase + trailing slash removal)"
    
    # Save deduplicated data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated_data, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Saved deduplicated links to: {output_file}")
    
    # Show breakdown by category
    print(f"\n📊 Final breakdown:")
    for category, urls in deduplicated_data['categorized'].items():
        print(f"   • {category.title()}: {len(urls)} links")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Comprehensive Web Scraper for Labellerr Website
Extracts all content from every page including text, metadata, and structure
"""

# import os
# import json
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse
# from datetime import datetime
# import time
# import logging

# # Setup logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# class LabellerrContentScraper:
#     def __init__(self, output_dir="data_ingest/raw"):
#         self.output_dir = output_dir
#         self.pages_dir = os.path.join(output_dir, "pages_content")
#         os.makedirs(self.pages_dir, exist_ok=True)
        
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         })
        
#         self.scraped_pages = []
#         self.failed_pages = []

#     def extract_page_metadata(self, soup, url):
#         """Extract metadata from the page"""
#         metadata = {
#             "url": url,
#             "scraped_at": datetime.now().isoformat(),
#             "title": "",
#             "description": "",
#             "keywords": "",
#             "page_type": self.categorize_page(url)
#         }
        
#         # Extract title
#         title_tag = soup.find('title')
#         if title_tag:
#             metadata["title"] = title_tag.get_text(strip=True)
        
#         # Extract meta description
#         desc_tag = soup.find('meta', {'name': 'description'})
#         if desc_tag:
#             metadata["description"] = desc_tag.get('content', '').strip()
        
#         # Extract keywords
#         keywords_tag = soup.find('meta', {'name': 'keywords'})
#         if keywords_tag:
#             metadata["keywords"] = keywords_tag.get('content', '').strip()
        
#         return metadata

#     def categorize_page(self, url):
#         """Categorize page type based on URL"""
#         path = urlparse(url).path.lower()
        
#         if '/blog' in path:
#             return 'blog'
#         elif any(x in path for x in ['/product', '/platform', '/annotation', '/video', '/image', '/text', '/dicom']):
#             return 'product'
#         elif any(x in path for x in ['/pricing', '/demo', '/book']):
#             return 'sales'
#         elif any(x in path for x in ['/about', '/careers', '/contact']):
#             return 'company'
#         elif any(x in path for x in ['/case-studies', '/vs-']):
#             return 'marketing'
#         elif any(x in path for x in ['/automotive', '/healthcare', '/retail', '/energy', '/manufacturing']):
#             return 'industry'
#         else:
#             return 'general'

#     def clean_content(self, soup):
#         """Clean and extract main content from page"""
#         # Remove unwanted elements
#         for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'form']):
#             element.decompose()
        
#         body = soup.body
#         if not body:
#             body = soup

#         text = body.get_text(separator=' ', strip=True)

#         # Collapse multiple whitespace into single spaces
#         import re
#         text = re.sub(r'\s+', ' ', text)
#         return text

#     def extract_structured_data(self, soup):
#         """Extract structured data like headings, lists, etc."""
#         structured = {
#             "headings": [],
#             "lists": [],
#             "links": [],
#             "images": []
#         }
        
#         # Extract headings
#         for level in range(1, 7):
#             for h in soup.find_all(f'h{level}'):
#                 structured["headings"].append({
#                     "level": level,
#                     "text": h.get_text(strip=True)
#                 })
        
#         # Extract lists
#         for ul in soup.find_all(['ul', 'ol']):
#             list_items = [li.get_text(strip=True) for li in ul.find_all('li')]
#             if list_items:
#                 structured["lists"].append(list_items)
        
#         # Extract internal links
#         for a in soup.find_all('a', href=True):
#             href = a.get('href', '')
#             if 'labellerr.com' in href:
#                 structured["links"].append({
#                     "url": href,
#                     "text": a.get_text(strip=True)
#                 })
        
#         # Extract images with alt text
#         for img in soup.find_all('img', alt=True):
#             structured["images"].append({
#                 "src": img.get('src', ''),
#                 "alt": img.get('alt', '')
#             })
        
#         return structured

#     def create_text_chunks(self, text, max_words=300):
#         """Split text into chunks for better processing"""
#         if not text:
#             return []
        
#         words = text.split()
#         chunks = []
#         for i in range(0, len(words), max_words):
#             chunk = " ".join(words[i:i + max_words])
#             if chunk.strip():
#                 chunks.append(chunk.strip())
#         return chunks

#     def scrape_page(self, url):
#         """Scrape a single page completely"""
#         try:
#             logger.info(f"Scraping: {url}")
#             response = self.session.get(url, timeout=15)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Extract all data
#             metadata = self.extract_page_metadata(soup, url)
#             clean_text = self.clean_content(soup)
#             structured_data = self.extract_structured_data(soup)
#             text_chunks = self.create_text_chunks(clean_text)
            
#             page_data = {
#                 "source_type": "webpage",
#                 "metadata": metadata,
#                 "full_text": clean_text,
#                 "structured_data": structured_data,
#                 "chunks": text_chunks,
#                 "chunk_count": len(text_chunks),
#                 "word_count": len(clean_text.split()),
#                 "content_length": len(clean_text)
#             }
            
#             return page_data
            
#         except Exception as e:
#             logger.error(f"Failed to scrape {url}: {e}")
#             self.failed_pages.append({"url": url, "error": str(e)})
#             return None

#     def scrape_all_pages(self, links_file):
#         """Scrape all pages from the links file"""
#         # Load links
#         with open(links_file, 'r', encoding='utf-8') as f:
#             data = json.load(f)
        
#         all_links = data.get('all_links', [])
#         logger.info(f"Starting to scrape {len(all_links)} pages...")
        
#         for i, url in enumerate(all_links, 1):
#             logger.info(f"[{i}/{len(all_links)}] Processing: {url}")
            
#             page_data = self.scrape_page(url)
#             if page_data:
#                 self.scraped_pages.append(page_data)
#                 logger.info(f"✅ Successfully scraped: {page_data['metadata']['title']}")
#             else:
#                 logger.warning(f"❌ Failed to scrape: {url}")
            
#             # Rate limiting - be respectful
#             time.sleep(1)
        
#         # Save results
#         self.save_results()

#     def save_results(self):
#         """Save all scraped content to files"""
#         # Save main content file
#         output_file = os.path.join(self.output_dir, "labellerr_all_pages_content.json")
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(self.scraped_pages, f, ensure_ascii=False, indent=2)
        
#         # Save failed pages
#         if self.failed_pages:
#             failed_file = os.path.join(self.output_dir, "failed_pages.json")
#             with open(failed_file, 'w', encoding='utf-8') as f:
#                 json.dump(self.failed_pages, f, ensure_ascii=False, indent=2)
        
#         # Save summary
#         summary = {
#             "scraping_completed_at": datetime.now().isoformat(),
#             "total_pages_attempted": len(self.scraped_pages) + len(self.failed_pages),
#             "successful_scrapes": len(self.scraped_pages),
#             "failed_scrapes": len(self.failed_pages),
#             "total_words": sum(page['word_count'] for page in self.scraped_pages),
#             "total_chunks": sum(page['chunk_count'] for page in self.scraped_pages),
#             "page_types": self.get_page_type_breakdown()
#         }
        
#         summary_file = os.path.join(self.output_dir, "scraping_summary.json")
#         with open(summary_file, 'w', encoding='utf-8') as f:
#             json.dump(summary, f, ensure_ascii=False, indent=2)
        
#         logger.info("✅ Scraping completed!")
#         logger.info(f"📊 Results: {len(self.scraped_pages)} successful, {len(self.failed_pages)} failed")
#         logger.info(f"📁 Saved to: {output_file}")
#         logger.info(f"📈 Total words: {summary['total_words']}")
#         logger.info(f"📝 Total chunks: {summary['total_chunks']}")

#     def get_page_type_breakdown(self):
#         """Get breakdown of pages by type"""
#         breakdown = {}
#         for page in self.scraped_pages:
#             page_type = page['metadata']['page_type']
#             breakdown[page_type] = breakdown.get(page_type, 0) + 1
#         return breakdown

# def main():
#     # Initialize scraper
#     scraper = LabellerrContentScraper()
    
#     # Path to your deduplicated links file
#     links_file = "data_ingest/raw/labellerr_homepage_links.json"
    
#     # Start scraping
#     scraper.scrape_all_pages(links_file)
    
#     print(f"\n🎉 Complete content extraction finished!")
#     print(f"📊 Check the summary file for detailed statistics")

# if __name__ == "__main__":
#     main()
