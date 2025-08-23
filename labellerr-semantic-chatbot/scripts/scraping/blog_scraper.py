# #!/usr/bin/env python3
# """
# Blog Content Scraper for Labellerr
# Extracts all blog posts from https://www.labellerr.com/blog/
# """

# import os
# import json
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse
# from datetime import datetime
# import time
# import re

# class LabellerrBlogScraper:
#     def __init__(self, output_dir="../../data_ingest/raw"):
#         self.output_dir = output_dir
#         self.blog_dir = os.path.join(output_dir, "blog")
#         os.makedirs(self.blog_dir, exist_ok=True)
        
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         })
        
#         self.blog_posts = []

#     def find_all_blog_links(self, blog_url="https://www.labellerr.com/blog/"):
#         """Find all blog post links from the blog listing page"""
#         print(f"🔍 Scanning blog page: {blog_url}")
        
#         try:
#             response = self.session.get(blog_url, timeout=15)
#             response.raise_for_status()
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Find all links that start with /blog/ (but not just /blog/ itself)
#             blog_links = set()
            
#             for a_tag in soup.find_all('a', href=True):
#                 href = a_tag['href']
                
#                 # Convert relative URLs to absolute
#                 full_url = urljoin(blog_url, href)
#                 parsed = urlparse(full_url)
                
#                 # Only include blog post URLs (not the main blog page)
#                 if (parsed.path.startswith('/blog/') and 
#                     parsed.path != '/blog/' and 
#                     parsed.path != '/blog' and
#                     'labellerr.com' in parsed.netloc):
#                     blog_links.add(full_url)
            
#             print(f"✅ Found {len(blog_links)} blog post links")
#             return sorted(list(blog_links))
            
#         except Exception as e:
#             print(f"❌ Error fetching blog listing: {e}")
#             return []

#     def extract_blog_metadata(self, soup, url):
#         """Extract metadata from a blog post"""
#         metadata = {
#             "url": url,
#             "scraped_at": datetime.now().isoformat(),
#             "title": "",
#             "excerpt": "",
#             "author": "",
#             "publish_date": "",
#             "tags": [],
#             "reading_time": ""
#         }
        
#         # Extract title (try multiple selectors)
#         title_selectors = ['h1', '.post-title', '.blog-title', 'title']
#         for selector in title_selectors:
#             title_elem = soup.select_one(selector)
#             if title_elem and title_elem.get_text(strip=True):
#                 metadata["title"] = title_elem.get_text(strip=True)
#                 break
        
#         # Extract meta description as excerpt
#         meta_desc = soup.find('meta', {'name': 'description'})
#         if meta_desc:
#             metadata["excerpt"] = meta_desc.get('content', '').strip()
        
#         # Try to find author
#         author_selectors = ['.author', '.post-author', '[class*="author"]', '[itemprop="author"]']
#         for selector in author_selectors:
#             author_elem = soup.select_one(selector)
#             if author_elem:
#                 metadata["author"] = author_elem.get_text(strip=True)
#                 break
        
#         # Try to find publish date
#         date_selectors = ['.date', '.publish-date', '.post-date', '[datetime]', 'time']
#         for selector in date_selectors:
#             date_elem = soup.select_one(selector)
#             if date_elem:
#                 date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
#                 metadata["publish_date"] = date_text
#                 break
        
#         # Extract tags
#         tag_selectors = ['.tags a', '.post-tags a', '[class*="tag"] a']
#         for selector in tag_selectors:
#             tags = soup.select(selector)
#             if tags:
#                 metadata["tags"] = [tag.get_text(strip=True) for tag in tags]
#                 break
        
#         return metadata

#     def clean_blog_content(self, soup):
#         """Extract and clean blog post content"""
#         # Remove unwanted elements
#         for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'form', '.sidebar', '.comments']):
#             element.decompose()
        
#         # Try to find main content area
#         content_selectors = [
#             'article',
#             '.post-content',
#             '.blog-content',
#             '.entry-content',
#             '.content',
#             'main',
#             '#content'
#         ]
        
#         content_element = None
#         for selector in content_selectors:
#             content_element = soup.select_one(selector)
#             if content_element:
#                 break
        
#         # Fallback to body if no content area found
#         if not content_element:
#             content_element = soup.find('body')
        
#         if content_element:
#             # Get text while preserving some structure
#             text = content_element.get_text(separator='\n', strip=True)
#             # Clean up excessive whitespace
#             text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines
#             text = re.sub(r' +', ' ', text)  # Replace multiple spaces
#             return text.strip()
        
#         return ""

#     def create_blog_chunks(self, content, max_words=400):
#         """Split blog content into chunks"""
#         if not content:
#             return []
        
#         # Split by paragraphs first
#         paragraphs = content.split('\n\n')
#         chunks = []
#         current_chunk = ""
        
#         for para in paragraphs:
#             para = para.strip()
#             if not para:
#                 continue
            
#             # If adding this paragraph would exceed limit, save current chunk
#             if current_chunk and len((current_chunk + ' ' + para).split()) > max_words:
#                 chunks.append(current_chunk.strip())
#                 current_chunk = para
#             else:
#                 current_chunk = current_chunk + '\n\n' + para if current_chunk else para
        
#         # Add the last chunk
#         if current_chunk.strip():
#             chunks.append(current_chunk.strip())
        
#         return chunks

#     def scrape_blog_post(self, url):
#         """Scrape a single blog post"""
#         try:
#             print(f"📖 Scraping blog post: {url}")
#             response = self.session.get(url, timeout=15)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Extract all data
#             metadata = self.extract_blog_metadata(soup, url)
#             content = self.clean_blog_content(soup)
#             chunks = self.create_blog_chunks(content)
            
#             blog_data = {
#                 "source_type": "blog_post",
#                 "metadata": metadata,
#                 "full_text": content,
#                 "chunks": chunks,
#                 "chunk_count": len(chunks),
#                 "word_count": len(content.split()),
#                 "content_length": len(content)
#             }
            
#             print(f"✅ Scraped: {metadata['title'][:50]}... ({len(chunks)} chunks)")
#             return blog_data
            
#         except Exception as e:
#             print(f"❌ Failed to scrape {url}: {e}")
#             return None

#     def scrape_all_blogs(self):
#         """Scrape all blog posts from Labellerr blog"""
#         # Step 1: Find all blog post URLs
#         blog_links = self.find_all_blog_links()
        
#         if not blog_links:
#             print("❌ No blog links found")
#             return
        
#         print(f"🚀 Starting to scrape {len(blog_links)} blog posts...")
        
#         # Step 2: Scrape each blog post
#         for i, url in enumerate(blog_links, 1):
#             print(f"\n[{i}/{len(blog_links)}] Processing: {url}")
            
#             blog_data = self.scrape_blog_post(url)
#             if blog_data:
#                 self.blog_posts.append(blog_data)
            
#             # Rate limiting - be respectful
#             time.sleep(1)
        
#         # Step 3: Save results
#         self.save_blog_results()

#     def save_blog_results(self):
#         """Save all blog content to files"""
#         if not self.blog_posts:
#             print("❌ No blog posts were successfully scraped")
#             return
        
#         # Save main blog content file
#         blog_file = os.path.join(self.blog_dir, "labellerr_blog_posts.json")
#         with open(blog_file, 'w', encoding='utf-8') as f:
#             json.dump(self.blog_posts, f, ensure_ascii=False, indent=2)
        
#         # Save blog summary
#         summary = {
#             "scraping_completed_at": datetime.now().isoformat(),
#             "total_blog_posts": len(self.blog_posts),
#             "total_words": sum(post['word_count'] for post in self.blog_posts),
#             "total_chunks": sum(post['chunk_count'] for post in self.blog_posts),
#             "average_words_per_post": sum(post['word_count'] for post in self.blog_posts) // len(self.blog_posts) if self.blog_posts else 0,
#             "blog_titles": [post['metadata']['title'] for post in self.blog_posts]
#         }
        
#         summary_file = os.path.join(self.blog_dir, "blog_summary.json")
#         with open(summary_file, 'w', encoding='utf-8') as f:
#             json.dump(summary, f, ensure_ascii=False, indent=2)
        
#         print(f"\n🎉 Blog scraping completed!")
#         print(f"📊 Results: {len(self.blog_posts)} blog posts scraped")
#         print(f"📁 Saved to: {blog_file}")
#         print(f"📈 Total words: {summary['total_words']}")
#         print(f"📝 Total chunks: {summary['total_chunks']}")
#         print(f"📊 Average words per post: {summary['average_words_per_post']}")

# def main():
#     """Main execution function"""
#     scraper = LabellerrBlogScraper()
#     scraper.scrape_all_blogs()

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
Complete Blog Content Extractor for Labellerr
Extracts full content from all blog post URLs with metadata and chunking
"""

# import os
# import json
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin, urlparse
# from datetime import datetime
# import time
# import re

# class BlogContentExtractor:
#     def __init__(self, output_dir="data_ingest/raw"):
#         self.output_dir = output_dir
#         self.blog_content_dir = os.path.join(output_dir, "blog_content")
#         os.makedirs(self.blog_content_dir, exist_ok=True)
        
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         })
        
#         self.extracted_posts = []
#         self.failed_urls = []

#     def extract_blog_metadata(self, soup, url):
#         """Extract metadata from blog post"""
#         metadata = {
#             "url": url,
#             "scraped_at": datetime.now().isoformat(),
#             "title": "",
#             "author": "",
#             "publish_date": "",
#             "tags": [],
#             "meta_description": "",
#             "reading_time": "",
#             "featured_image": ""
#         }
        
#         # Extract title
#         title_selectors = [
#             'h1.post-title',
#             'h1.entry-title', 
#             '.post-header h1',
#             'article h1',
#             'h1'
#         ]
        
#         for selector in title_selectors:
#             title_elem = soup.select_one(selector)
#             if title_elem and title_elem.get_text(strip=True):
#                 metadata["title"] = title_elem.get_text(strip=True)
#                 break
        
#         # Extract meta description
#         meta_desc = soup.find('meta', {'name': 'description'})
#         if meta_desc:
#             metadata["meta_description"] = meta_desc.get('content', '').strip()
        
#         # Extract author
#         author_selectors = [
#             '.author-name',
#             '.post-author',
#             '[rel="author"]',
#             '.byline',
#             '[class*="author"]'
#         ]
        
#         for selector in author_selectors:
#             author_elem = soup.select_one(selector)
#             if author_elem:
#                 metadata["author"] = author_elem.get_text(strip=True)
#                 break
        
#         # Extract publish date
#         date_selectors = [
#             'time[datetime]',
#             '.publish-date',
#             '.post-date',
#             '[class*="date"]'
#         ]
        
#         for selector in date_selectors:
#             date_elem = soup.select_one(selector)
#             if date_elem:
#                 date_text = date_elem.get('datetime') or date_elem.get_text(strip=True)
#                 metadata["publish_date"] = date_text
#                 break
        
#         # Extract tags
#         tag_selectors = [
#             '.post-tags a',
#             '.tags a',
#             '[class*="tag"] a',
#             '.categories a'
#         ]
        
#         for selector in tag_selectors:
#             tag_elements = soup.select(selector)
#             if tag_elements:
#                 metadata["tags"] = [tag.get_text(strip=True) for tag in tag_elements]
#                 break
        
#         # Extract featured image
#         img_selectors = [
#             '.featured-image img',
#             '.post-image img',
#             'article img'
#         ]
        
#         for selector in img_selectors:
#             img_elem = soup.select_one(selector)
#             if img_elem:
#                 src = img_elem.get('src') or img_elem.get('data-src')
#                 if src:
#                     metadata["featured_image"] = urljoin(url, src)
#                     break
        
#         return metadata

#     def clean_blog_content(self, soup):
#         """Extract and clean blog post content"""
#         # Remove unwanted elements
#         unwanted_selectors = [
#             'script', 'style', 'nav', 'footer', 'header', 'aside', 
#             'noscript', 'form', '.sidebar', '.comments', '.related-posts',
#             '.share-buttons', '.advertisement', '.ads', '.social-share',
#             '.newsletter-signup', '.author-bio', '.pagination'
#         ]
        
#         for selector in unwanted_selectors:
#             for element in soup.select(selector):
#                 element.decompose()
        
#         # Find main content
#         content_selectors = [
#             'article .post-content',
#             'article .entry-content',
#             '.blog-post-content',
#             '.post-body',
#             'article',
#             '.content',
#             'main'
#         ]
        
#         content_element = None
#         for selector in content_selectors:
#             content_element = soup.select_one(selector)
#             if content_element:
#                 break
        
#         if not content_element:
#             content_element = soup.find('body')
        
#         if content_element:
#             # Clean up the text
#             text = content_element.get_text(separator='\n', strip=True)
            
#             # Clean excessive whitespace
#             text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines
#             text = re.sub(r' +', ' ', text)  # Multiple spaces
#             text = re.sub(r'\t+', ' ', text)  # Tabs
            
#             return text.strip()
        
#         return ""

#     def create_content_chunks(self, content, max_words=300):
#         """Split content into chunks for embeddings"""
#         if not content:
#             return []
        
#         # Split by paragraphs first
#         paragraphs = content.split('\n\n')
#         chunks = []
#         current_chunk = ""
        
#         for para in paragraphs:
#             para = para.strip()
#             if not para:
#                 continue
            
#             # Check word count if we add this paragraph
#             test_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
#             word_count = len(test_chunk.split())
            
#             if word_count > max_words and current_chunk:
#                 # Save current chunk and start new one
#                 chunks.append(current_chunk.strip())
#                 current_chunk = para
#             else:
#                 current_chunk = test_chunk
        
#         # Add the last chunk
#         if current_chunk.strip():
#             chunks.append(current_chunk.strip())
        
#         return chunks

#     def extract_single_post(self, url):
#         """Extract content from a single blog post"""
#         try:
#             print(f"📖 Extracting: {url}")
            
#             response = self.session.get(url, timeout=15)
#             response.raise_for_status()
            
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Extract metadata
#             metadata = self.extract_blog_metadata(soup, url)
            
#             # Extract content
#             content = self.clean_blog_content(soup)
            
#             # Create chunks
#             chunks = self.create_content_chunks(content)
            
#             # Structure the data
#             post_data = {
#                 "source_type": "blog_post",
#                 "metadata": metadata,
#                 "full_text": content,
#                 "chunks": chunks,
#                 "chunk_count": len(chunks),
#                 "word_count": len(content.split()) if content else 0,
#                 "content_length": len(content) if content else 0
#             }
            
#             print(f"✅ Extracted: {metadata['title'][:50]}... ({len(chunks)} chunks, {post_data['word_count']} words)")
#             return post_data
            
#         except Exception as e:
#             print(f"❌ Failed to extract {url}: {e}")
#             self.failed_urls.append({"url": url, "error": str(e)})
#             return None

#     def extract_all_blog_content(self, links_file_path):
#         """Extract content from all blog post URLs"""
#         # Load blog links
#         print(f"📂 Loading blog links from: {links_file_path}")
        
#         with open(links_file_path, 'r', encoding='utf-8') as f:
#             blog_urls = json.load(f)
        
#         print(f"🚀 Starting extraction from {len(blog_urls)} blog posts...")
        
#         for i, url in enumerate(blog_urls, 1):
#             print(f"\n[{i}/{len(blog_urls)}] Processing: {url}")
            
#             post_data = self.extract_single_post(url)
#             if post_data:
#                 self.extracted_posts.append(post_data)
            
#             # Rate limiting - be respectful
#             time.sleep(1)
        
#         # Save results
#         self.save_all_results()

#     def save_all_results(self):
#         """Save all extracted blog content"""
#         if not self.extracted_posts:
#             print("❌ No blog posts were successfully extracted")
#             return
        
#         # Main content file
#         content_file = os.path.join(self.blog_content_dir, "all_blog_posts_content.json")
#         with open(content_file, 'w', encoding='utf-8') as f:
#             json.dump(self.extracted_posts, f, ensure_ascii=False, indent=2)
        
#         # Failed URLs file
#         if self.failed_urls:
#             failed_file = os.path.join(self.blog_content_dir, "failed_blog_extractions.json")
#             with open(failed_file, 'w', encoding='utf-8') as f:
#                 json.dump(self.failed_urls, f, ensure_ascii=False, indent=2)
        
#         # Summary file
#         summary = {
#             "extraction_completed_at": datetime.now().isoformat(),
#             "total_posts_attempted": len(self.extracted_posts) + len(self.failed_urls),
#             "successful_extractions": len(self.extracted_posts),
#             "failed_extractions": len(self.failed_urls),
#             "total_words": sum(post['word_count'] for post in self.extracted_posts),
#             "total_chunks": sum(post['chunk_count'] for post in self.extracted_posts),
#             "average_words_per_post": sum(post['word_count'] for post in self.extracted_posts) // len(self.extracted_posts) if self.extracted_posts else 0,
#             "top_authors": self.get_top_authors(),
#             "common_tags": self.get_common_tags()
#         }
        
#         summary_file = os.path.join(self.blog_content_dir, "blog_extraction_summary.json")
#         with open(summary_file, 'w', encoding='utf-8') as f:
#             json.dump(summary, f, ensure_ascii=False, indent=2)
        
#         print(f"\n🎉 Blog content extraction completed!")
#         print(f"📊 Results:")
#         print(f"   • Successfully extracted: {len(self.extracted_posts)} posts")
#         print(f"   • Failed extractions: {len(self.failed_urls)} posts")
#         print(f"   • Total words: {summary['total_words']:,}")
#         print(f"   • Total chunks: {summary['total_chunks']}")
#         print(f"   • Average words per post: {summary['average_words_per_post']}")
#         print(f"📁 Files saved:")
#         print(f"   • Main content: {content_file}")
#         print(f"   • Summary: {summary_file}")
#         if self.failed_urls:
#             print(f"   • Failed URLs: {failed_file}")

#     def get_top_authors(self):
#         """Get top authors by post count"""
#         author_counts = {}
#         for post in self.extracted_posts:
#             author = post['metadata']['author']
#             if author:
#                 author_counts[author] = author_counts.get(author, 0) + 1
#         return dict(sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10])

#     def get_common_tags(self):
#         """Get most common tags"""
#         tag_counts = {}
#         for post in self.extracted_posts:
#             for tag in post['metadata']['tags']:
#                 if tag:
#                     tag_counts[tag] = tag_counts.get(tag, 0) + 1
#         return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20])

# def main():
#     """Main execution function"""
#     # Initialize extractor
#     extractor = BlogContentExtractor()
    
#     # Path to your blog links file (update this path)
#     links_file = "../../data_ingest/raw/blog/playwright_blog_links.json"
#     # Alternative paths if the above doesn't exist:
#     # links_file = "../../data_ingest/raw/blog/all_blog_links_complete.json"
#     # links_file = "../../data_ingest/raw/blog/playwright_blog_links.json"
    
#     # Check if file exists
#     if not os.path.exists(links_file):
#         print(f"❌ Links file not found: {links_file}")
#         print("Please update the 'links_file' path to your actual blog links JSON file")
#         return
    
#     # Extract all blog content
#     extractor.extract_all_blog_content(links_file)

# if __name__ == "__main__":
#     main()



# #!/usr/bin/env python3
# """
# Playwright Blog Scraper - Better than Selenium for infinite scroll
# """
import asyncio
from playwright.async_api import async_playwright
import json
import os

async def extract_blog_links_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto("https://www.labellerr.com/blog/", wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print("🚀 Starting Playwright infinite scroll...")
        
        prev_height = -1
        max_scrolls = 1000
        scroll_count = 0
        no_change_count = 0
        
        while scroll_count < max_scrolls and no_change_count < 15:
            # Scroll to bottom
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(3000)  # Wait for content to load
            
            # Check if height changed
            curr_height = await page.evaluate('document.body.scrollHeight')
            
            if curr_height == prev_height:
                no_change_count += 1
                print(f"⏳ No change #{no_change_count} at scroll {scroll_count}")
                await page.wait_for_timeout(2000)  # Wait longer
            else:
                no_change_count = 0
                prev_height = curr_height
                print(f"📈 Scroll {scroll_count}: Height = {curr_height}")
            
            scroll_count += 1
            
            # Check current progress
            if scroll_count % 50 == 0:
                links = await page.eval_on_selector_all(
                    'a[href^="/blog/"]', 
                    'elements => elements.map(el => el.href)'
                )
                unique_links = list(set([link for link in links if not link.endswith('/blog/') and not link.endswith('/blog')]))
                print(f"🔗 Progress: {len(unique_links)} links found")
        
        # Extract all links
        all_links = await page.eval_on_selector_all(
            'a[href^="/blog/"]', 
            'elements => elements.map(el => el.href)'
        )
        
        # Filter and deduplicate
        unique_links = list(set([
            link for link in all_links 
            if not link.endswith('/blog/') and not link.endswith('/blog')
        ]))
        
        unique_links.sort()
        
        # Save results
        output_dir = "../../data_ingest/raw/blog"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "playwright_blog_links.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_links, f, indent=2)
        
        await browser.close()
        
        print(f"✅ PLAYWRIGHT COMPLETE: {len(unique_links)} blog links extracted!")
        print(f"📁 Saved to: {output_file}")
        
        return unique_links

# Run the async function
if __name__ == "__main__":
    asyncio.run(extract_blog_links_playwright())
