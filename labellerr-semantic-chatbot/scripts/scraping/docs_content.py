# #!/usr/bin/env python3
# """
# Documentation Headings Extractor: Extract and Deduplicate All Headings
# """

# import os
# import json
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin
# import time

# class HeadingsExtractor:
#     def __init__(self, base_url="https://docs.labellerr.com/", output_dir="../../data_ingest/raw"):
#         self.base_url = base_url
#         self.output_dir = output_dir
#         self.docs_dir = os.path.join(output_dir, "documentation_sections")
#         os.makedirs(self.docs_dir, exist_ok=True)
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#         })

#     def discover_pages(self):
#         """Discover all documentation page URLs"""
#         print(f"🔍 Discovering pages from: {self.base_url}")
#         resp = self.session.get(self.base_url, timeout=15)
#         resp.raise_for_status()
#         soup = BeautifulSoup(resp.text, 'html.parser')
        
#         links = set()
#         for a in soup.find_all('a', href=True):
#             href = a['href'].strip()
#             if href.startswith('/'):
#                 full = urljoin(self.base_url, href)
#             elif href.startswith(self.base_url):
#                 full = href
#             else:
#                 continue
#             if 'documentation-labellerr' in full:
#                 links.add(full)
        
#         print(f"✅ Found {len(links)} documentation pages")
#         return sorted(links)

#     def extract_headings_from_page(self, url):
#         """Extract only headings from a single page"""
#         try:
#             print(f"📖 Extracting headings from: {url}")
#             resp = self.session.get(url, timeout=15)
#             resp.raise_for_status()
#             soup = BeautifulSoup(resp.text, 'html.parser')

#             # Remove unwanted elements first
#             for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
#                 tag.decompose()

#             # Extract all headings
#             headings = []
#             for heading_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
#                 level = int(heading_tag.name[1])
#                 title = heading_tag.get_text(strip=True)
                
#                 if title:  # Only non-empty headings
#                     headings.append({
#                         "heading": title,
#                         "level": level,
#                         "url": url
#                     })
            
#             print(f"   Found {len(headings)} headings")
#             return headings
            
#         except Exception as e:
#             print(f"❌ Failed to extract from {url}: {e}")
#             return []

#     def extract_all_headings(self):
#         """Extract headings from all documentation pages"""
#         pages = self.discover_pages()
#         all_headings = []
        
#         print(f"\n🚀 Starting headings extraction from {len(pages)} pages...\n")
        
#         for i, url in enumerate(pages, 1):
#             print(f"[{i}/{len(pages)}] Processing: {url}")
#             headings = self.extract_headings_from_page(url)
#             all_headings.extend(headings)
            
#             # Rate limiting
#             time.sleep(0.5)
        
#         return all_headings

#     def deduplicate_headings(self, all_headings):
#         """Remove duplicate headings while preserving metadata"""
#         print(f"\n📊 Processing {len(all_headings)} total headings...")
        
#         # Group by heading text (case-insensitive)
#         heading_groups = {}
#         for heading in all_headings:
#             key = heading['heading'].lower().strip()
#             if key not in heading_groups:
#                 heading_groups[key] = []
#             heading_groups[key].append(heading)
        
#         # Create deduplicated list
#         unique_headings = []
#         for key, group in heading_groups.items():
#             # Take the first occurrence but collect all URLs where it appears
#             main_heading = group[0].copy()
#             main_heading['appears_on_urls'] = [item['url'] for item in group]
#             main_heading['frequency'] = len(group)
#             unique_headings.append(main_heading)
        
#         # Sort by level, then alphabetically
#         unique_headings.sort(key=lambda x: (x['level'], x['heading'].lower()))
        
#         print(f"✅ Deduplicated to {len(unique_headings)} unique headings")
#         return unique_headings

#     def save_headings(self, all_headings, unique_headings):
#         """Save both raw and deduplicated headings"""
        
#         # Save all headings (raw)
#         all_headings_file = os.path.join(self.docs_dir, "all_headings_raw.json")
#         with open(all_headings_file, 'w', encoding='utf-8') as f:
#             json.dump(all_headings, f, ensure_ascii=False, indent=2)
        
#         # Save unique headings (deduplicated)
#         unique_headings_file = os.path.join(self.docs_dir, "unique_headings.json")
#         with open(unique_headings_file, 'w', encoding='utf-8') as f:
#             json.dump(unique_headings, f, ensure_ascii=False, indent=2)
        
#         # Save simple list of heading texts
#         heading_texts = [h['heading'] for h in unique_headings]
#         simple_list_file = os.path.join(self.docs_dir, "headings_list.txt")
#         with open(simple_list_file, 'w', encoding='utf-8') as f:
#             for heading in heading_texts:
#                 f.write(f"{heading}\n")
        
#         # Create summary
#         summary = {
#             "extraction_date": time.strftime("%Y-%m-%d %H:%M:%S"),
#             "total_headings_found": len(all_headings),
#             "unique_headings": len(unique_headings),
#             "duplicates_removed": len(all_headings) - len(unique_headings),
#             "heading_levels_breakdown": self.get_level_breakdown(unique_headings),
#             "most_frequent_headings": self.get_most_frequent(unique_headings)
#         }
        
#         summary_file = os.path.join(self.docs_dir, "headings_summary.json")
#         with open(summary_file, 'w', encoding='utf-8') as f:
#             json.dump(summary, f, ensure_ascii=False, indent=2)
        
#         print(f"\n📁 Files saved:")
#         print(f"   • Raw headings: {all_headings_file}")
#         print(f"   • Unique headings: {unique_headings_file}")
#         print(f"   • Simple list: {simple_list_file}")
#         print(f"   • Summary: {summary_file}")
        
#         return summary

#     def get_level_breakdown(self, headings):
#         """Get breakdown of headings by level"""
#         levels = {}
#         for h in headings:
#             level = f"h{h['level']}"
#             levels[level] = levels.get(level, 0) + 1
#         return levels

#     def get_most_frequent(self, headings):
#         """Get headings that appear most frequently across pages"""
#         frequent = [h for h in headings if h['frequency'] > 1]
#         frequent.sort(key=lambda x: x['frequency'], reverse=True)
#         return frequent[:10]  # Top 10 most frequent

#     def print_sample_headings(self, unique_headings, limit=20):
#         """Print sample of unique headings"""
#         print(f"\n📋 Sample of unique headings (first {limit}):")
#         for i, heading in enumerate(unique_headings[:limit], 1):
#             freq_info = f" (appears {heading['frequency']}x)" if heading['frequency'] > 1 else ""
#             print(f"{i:2}. [H{heading['level']}] {heading['heading']}{freq_info}")

#     def run(self):
#         """Main execution method"""
#         print("🚀 Starting Documentation Headings Extraction...")
        
#         # Extract all headings
#         all_headings = self.extract_all_headings()
        
#         if not all_headings:
#             print("❌ No headings found!")
#             return
        
#         # Deduplicate
#         unique_headings = self.deduplicate_headings(all_headings)
        
#         # Save results
#         summary = self.save_headings(all_headings, unique_headings)
        
#         # Print sample
#         self.print_sample_headings(unique_headings)
        
#         print(f"\n🎉 Headings extraction completed!")
#         print(f"📊 Summary:")
#         print(f"   • Total headings found: {summary['total_headings_found']}")
#         print(f"   • Unique headings: {summary['unique_headings']}")
#         print(f"   • Duplicates removed: {summary['duplicates_removed']}")
#         print(f"   • Heading levels: {summary['heading_levels_breakdown']}")

# if __name__ == "__main__":
#     extractor = HeadingsExtractor()
#     extractor.run()


#!/usr/bin/env python3
"""
Complete Documentation Content Extractor for Labellerr Docs
Uses Selenium for JavaScript-heavy documentation sites
"""

import os
import json
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LabellerrDocsExtractor:
    def __init__(self, output_dir="../../data_ingest/raw/documentation_sections"):
        self.base_url = "https://docs.labellerr.com/"
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup Selenium
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        # Results storage
        self.extracted_sections = []
        self.failed_extractions = []
        self.discovered_pages = []

    def create_driver(self):
        """Create a new Chrome driver instance"""
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            return driver
        except Exception as e:
            print(f"❌ Failed to create Chrome driver: {e}")
            print("Please ensure ChromeDriver is installed and in PATH")
            return None

    def discover_all_documentation_pages(self):
        """Discover all documentation pages using Selenium"""
        print(f"🔍 Discovering documentation pages from: {self.base_url}")
        
        driver = self.create_driver()
        if not driver:
            return []
        
        try:
            driver.get(self.base_url)
            time.sleep(5)  # Wait for page to load
            
            # Wait for navigation elements to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            
            # Get page source after JavaScript execution
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            links = set()
            
            # Find all internal documentation links
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                
                if href.startswith('/'):
                    full_url = f"https://docs.labellerr.com{href}"
                elif href.startswith('https://docs.labellerr.com'):
                    full_url = href
                else:
                    continue
                
                # Only include actual documentation pages
                if 'documentation-labellerr' in full_url:
                    links.add(full_url)
            
            self.discovered_pages = sorted(list(links))
            print(f"✅ Discovered {len(self.discovered_pages)} documentation pages")
            
            return self.discovered_pages
            
        except Exception as e:
            print(f"❌ Error discovering pages: {e}")
            return []
        finally:
            driver.quit()

    def extract_page_content_with_selenium(self, url):
        """Extract content from a single page using Selenium"""
        driver = self.create_driver()
        if not driver:
            return None
        
        try:
            print(f"📖 Extracting content from: {url}")
            
            # Load the page
            driver.get(url)
            time.sleep(5)  # Wait for content to load
            
            # Try to wait for content to appear
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            # Get page source after JavaScript execution
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract page metadata
            page_title = self.extract_page_title(soup, url)
            
            # Extract sections with headings and content
            sections = self.extract_sections_from_soup(soup)
            
            # Calculate total content
            total_content = "\n".join([section['content'] for section in sections])
            word_count = len(total_content.split()) if total_content else 0
            
            page_data = {
                "url": url,
                "page_title": page_title,
                "sections": sections,
                "total_word_count": word_count,
                "section_count": len(sections),
                "extracted_at": datetime.now().isoformat()
            }
            
            print(f"   ✅ Extracted {len(sections)} sections ({word_count} total words)")
            return page_data
            
        except Exception as e:
            print(f"   ❌ Failed to extract from {url}: {e}")
            self.failed_extractions.append({
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return None
        finally:
            driver.quit()

    def extract_page_title(self, soup, url):
        """Extract page title"""
        # Try different title sources
        title_selectors = [
            'h1',
            'title',
            '.page-title',
            '.doc-title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and title != "Labellerr Documentation | Labellerr Docs":
                    return title
        
        # Fallback to URL-based title
        return url.split('/')[-1].replace('-', ' ').title()

    def extract_sections_from_soup(self, soup):
        """Extract sections with headings and content from soup"""
        # Remove unwanted elements
        self.clean_soup_for_content(soup)
        
        # Find all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            # If no headings found, try to extract any meaningful content
            return self.extract_content_without_headings(soup)
        
        sections = []
        
        for i, heading in enumerate(headings):
            heading_text = heading.get_text(strip=True)
            heading_level = int(heading.name[1])
            
            if not heading_text:
                continue
            
            # Extract content under this heading
            content = self.extract_content_under_heading(soup, heading, heading_level)
            
            # Create chunks for embedding
            chunks = self.create_content_chunks(content)
            
            section_data = {
                "heading": heading_text,
                "level": heading_level,
                "content": content,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "word_count": len(content.split()) if content else 0
            }
            
            sections.append(section_data)
        
        return sections

    def extract_content_without_headings(self, soup):
        """Extract content when no clear headings are found"""
        # Look for main content areas
        content_selectors = [
            'main',
            'article',
            '.content',
            '.documentation',
            '.doc-content',
            '.page-content',
            '.markdown-body',
            'body'
        ]
        
        content_text = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content_text = content_elem.get_text(separator='\n', strip=True)
                if len(content_text) > 100:  # Only if substantial content
                    break
        
        # Filter out navigation and UI text
        content_text = self.filter_navigation_text(content_text)
        
        if content_text:
            chunks = self.create_content_chunks(content_text)
            return [{
                "heading": "Main Content",
                "level": 1,
                "content": content_text,
                "chunks": chunks,
                "chunk_count": len(chunks),
                "word_count": len(content_text.split())
            }]
        
        return []

    def clean_soup_for_content(self, soup):
        """Remove unwanted elements from soup"""
        unwanted_selectors = [
            'script', 'style', 'nav', 'footer', 'header', 'aside',
            'noscript', 'form', '.sidebar', '.navigation', '.menu',
            '.breadcrumb', '.search', '.theme-switcher', '.ads',
            '.social-share', '.pagination', '.toc'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()

    def extract_content_under_heading(self, soup, heading_element, heading_level):
        """Extract content under a specific heading"""
        content_parts = []
        
        # Get all siblings after the heading
        for sibling in heading_element.next_siblings:
            # Stop at next heading of same or higher level
            if (isinstance(sibling, Tag) and 
                sibling.name and 
                sibling.name.startswith('h') and 
                int(sibling.name[1]) <= heading_level):
                break
            
            # Extract text from content elements
            if isinstance(sibling, Tag):
                if sibling.name in ['p', 'div', 'ul', 'ol', 'pre', 'code', 'blockquote', 'table', 'section']:
                    text = sibling.get_text(separator=' ', strip=True)
                    if text and len(text) > 5:  # Only meaningful text
                        content_parts.append(text)
                        
            elif isinstance(sibling, NavigableString):
                text = str(sibling).strip()
                if text and len(text) > 5:
                    content_parts.append(text)
        
        # If no content found after heading, try to get content from parent container
        if not content_parts:
            parent = heading_element.parent
            if parent:
                text = parent.get_text(separator=' ', strip=True)
                # Remove the heading text itself
                text = text.replace(heading_element.get_text(strip=True), '', 1).strip()
                if text and len(text) > 20:
                    content_parts.append(text)
        
        full_content = '\n\n'.join(content_parts).strip()
        
        # Filter out navigation text
        full_content = self.filter_navigation_text(full_content)
        
        return full_content

    def filter_navigation_text(self, text):
        """Filter out navigation and UI text"""
        if not text:
            return ""
        
        # Common navigation patterns to remove
        nav_patterns = [
            'Getting Started', 'Feature Demos', 'Actions', 'SDK Documentation',
            'Search', 'Theme switcher', 'Product Demo', 'Product Release',
            'Frequently accessed Tutorials', 'Few Additional Features',
            'Copy from similar images', 'Labellerr Grouping Tool Feature'
        ]
        
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip navigation patterns
            if any(pattern in line for pattern in nav_patterns):
                continue
                
            # Keep lines that are substantial content
            if len(line) > 15 and not line.isupper():
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def create_content_chunks(self, content, max_words=350):
        """Split content into chunks for embeddings"""
        if not content:
            return []
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Check if adding this paragraph exceeds word limit
            test_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
            word_count = len(test_chunk.split())
            
            if word_count > max_words and current_chunk:
                # Save current chunk and start new one
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk = test_chunk
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def extract_all_documentation(self):
        """Extract content from all documentation pages"""
        # Discover all pages
        pages = self.discover_all_documentation_pages()
        
        if not pages:
            print("❌ No documentation pages found!")
            return
        
        print(f"\n🚀 Starting content extraction from {len(pages)} pages...\n")
        
        # Extract content from each page
        for i, url in enumerate(pages, 1):
            print(f"\n[{i}/{len(pages)}] Processing page...")
            
            page_data = self.extract_page_content_with_selenium(url)
            if page_data:
                # Flatten sections for storage
                for section in page_data['sections']:
                    section_with_url = section.copy()
                    section_with_url['url'] = url
                    section_with_url['page_title'] = page_data['page_title']
                    self.extracted_sections.append(section_with_url)
            
            # Rate limiting between requests
            time.sleep(2)
        
        # Save results
        self.save_all_results()

    def save_all_results(self):
        """Save extracted content to files"""
        if not self.extracted_sections:
            print("❌ No content was extracted!")
            return
        
        # Main content file
        content_file = os.path.join(self.output_dir, "documentation_complete_with_selenium.json")
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_sections, f, ensure_ascii=False, indent=2)
        
        # Failed extractions
        if self.failed_extractions:
            failed_file = os.path.join(self.output_dir, "failed_extractions_selenium.json")
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_extractions, f, ensure_ascii=False, indent=2)
        
        # Summary
        summary = {
            "extraction_completed_at": datetime.now().isoformat(),
            "total_pages_discovered": len(self.discovered_pages),
            "total_sections_extracted": len(self.extracted_sections),
            "failed_extractions": len(self.failed_extractions),
            "total_words": sum(section['word_count'] for section in self.extracted_sections),
            "total_chunks": sum(section['chunk_count'] for section in self.extracted_sections),
            "average_words_per_section": sum(section['word_count'] for section in self.extracted_sections) // len(self.extracted_sections) if self.extracted_sections else 0,
            "sections_by_level": self.get_sections_by_level(),
            "top_sections_by_content": self.get_top_sections_by_content()
        }
        
        summary_file = os.path.join(self.output_dir, "extraction_summary_selenium.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Simple text export for review
        text_export_file = os.path.join(self.output_dir, "all_documentation_text.txt")
        with open(text_export_file, 'w', encoding='utf-8') as f:
            for section in self.extracted_sections:
                f.write(f"{'='*50}\n")
                f.write(f"URL: {section['url']}\n")
                f.write(f"HEADING: {section['heading']} (Level {section['level']})\n")
                f.write(f"WORDS: {section['word_count']}\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"{section['content']}\n\n")
        
        print(f"\n🎉 Documentation extraction completed!")
        print(f"📊 Results:")
        print(f"   • Pages discovered: {len(self.discovered_pages)}")
        print(f"   • Sections extracted: {len(self.extracted_sections)}")
        print(f"   • Failed extractions: {len(self.failed_extractions)}")
        print(f"   • Total words: {summary['total_words']:,}")
        print(f"   • Total chunks: {summary['total_chunks']}")
        print(f"   • Average words per section: {summary['average_words_per_section']}")
        print(f"📁 Files saved:")
        print(f"   • Main content: {content_file}")
        print(f"   • Text export: {text_export_file}")
        print(f"   • Summary: {summary_file}")
        if self.failed_extractions:
            print(f"   • Failed extractions: {failed_file}")

    def get_sections_by_level(self):
        """Get breakdown of sections by heading level"""
        levels = {}
        for section in self.extracted_sections:
            level = f"h{section['level']}"
            levels[level] = levels.get(level, 0) + 1
        return levels

    def get_top_sections_by_content(self):
        """Get sections with most content"""
        sorted_sections = sorted(
            self.extracted_sections, 
            key=lambda x: x['word_count'], 
            reverse=True
        )
        return [
            {
                "heading": section['heading'],
                "word_count": section['word_count'],
                "url": section['url']
            }
            for section in sorted_sections[:10]
        ]

    def run_simple_discovery(self):
        """Simple method to just discover pages without full extraction"""
        pages = self.discover_all_documentation_pages()
        
        # Save discovered pages
        pages_file = os.path.join(self.output_dir, "discovered_pages.json")
        with open(pages_file, 'w', encoding='utf-8') as f:
            json.dump(pages, f, indent=2)
        
        print(f"📁 Discovered {len(pages)} pages, saved to: {pages_file}")
        return pages

def main():
    """Main execution function"""
    print("🚀 Starting Labellerr Documentation Extraction with Selenium...")
    print("⚠️  Make sure ChromeDriver is installed and in PATH")
    
    extractor = LabellerrDocsExtractor()
    
    # Option 1: Full extraction (recommended)
    extractor.extract_all_documentation()
    
    # Option 2: Just discover pages first (for testing)
    # pages = extractor.run_simple_discovery()

if __name__ == "__main__":
    main()