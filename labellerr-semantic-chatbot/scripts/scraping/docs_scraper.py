#!/usr/bin/env python3
"""
Extract All Headings and Links from Labellerr Documentation
Simple focused script to map out documentation structure
"""

import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

class DocumentationHeadingsExtractor:
    def __init__(self, output_dir="data_ingest/raw/documentation"):
        self.base_url = "https://docs.labellerr.com/"
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
        self.all_headings = []

    def create_driver(self):
        """Create Chrome driver with automatic management"""
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            return driver
        except Exception as e:
            print(f"❌ Failed to create Chrome driver: {e}")
            return None

    def extract_page_links(self):
        """Extract all documentation page links from homepage"""
        print(f"🔍 Discovering documentation pages...")
        
        driver = self.create_driver()
        if not driver:
            return []
        
        page_links = set()
        
        try:
            driver.get(self.base_url)
            time.sleep(5)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find all internal documentation links
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href'].strip()
                
                # Convert to absolute URL
                if href.startswith('/'):
                    full_url = f"https://docs.labellerr.com{href}"
                elif href.startswith('https://docs.labellerr.com'):
                    full_url = href
                else:
                    continue
                
                # Filter for documentation pages
                if self.is_doc_page(full_url):
                    page_links.add(full_url)
            
            # Also add the homepage
            page_links.add(self.base_url)
            
        except Exception as e:
            print(f"❌ Error discovering pages: {e}")
        finally:
            driver.quit()
        
        return sorted(list(page_links))

    def is_doc_page(self, url):
        """Check if URL is a documentation page"""
        url_lower = url.lower()
        
        # Include patterns
        include_patterns = [
            '/documentation', '/labellerr/', '/getting-started', 
            '/feature-demos', '/actions', '/sdk'
        ]
        
        # Exclude patterns  
        exclude_patterns = [
            '.pdf', '.jpg', '.png', '.gif', 'search', 'login'
        ]
        
        has_include = any(pattern in url_lower for pattern in include_patterns)
        has_exclude = any(pattern in url_lower for pattern in exclude_patterns)
        
        return has_include and not has_exclude

    def extract_headings_from_page(self, url):
        """Extract all headings from a single page"""
        print(f"📖 Extracting headings from: {url}")
        
        driver = self.create_driver()
        if not driver:
            return []
        
        page_headings = []
        
        try:
            driver.get(url)
            time.sleep(3)
            
            # Wait for content to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract all heading elements
            for heading_tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading_tag.get_text(strip=True)
                
                if heading_text and len(heading_text) > 2:  # Skip very short headings
                    # Try to find associated link
                    heading_url = self.find_heading_link(heading_tag, url)
                    
                    heading_data = {
                        "heading": heading_text,
                        "level": int(heading_tag.name[1]),  # h1=1, h2=2, etc.
                        "url": heading_url,
                        "page_url": url,
                        "heading_tag": heading_tag.name
                    }
                    
                    page_headings.append(heading_data)
            
            print(f"  ✅ Found {len(page_headings)} headings")
            
        except Exception as e:
            print(f"  ❌ Error extracting from {url}: {e}")
        finally:
            driver.quit()
        
        return page_headings

    def find_heading_link(self, heading_tag, base_url):
        """Find URL associated with a heading"""
        # Check if heading itself is a link
        if heading_tag.name == 'a' or heading_tag.find('a'):
            link = heading_tag if heading_tag.name == 'a' else heading_tag.find('a')
            href = link.get('href', '')
            if href:
                return self.normalize_url(href, base_url)
        
        # Check if heading has an ID (for anchor links)
        heading_id = heading_tag.get('id')
        if heading_id:
            return f"{base_url}#{heading_id}"
        
        # Check for nearby links
        next_sibling = heading_tag.find_next_sibling('a')
        if next_sibling and next_sibling.get('href'):
            href = next_sibling.get('href')
            return self.normalize_url(href, base_url)
        
        # Default to the page URL
        return base_url

    def normalize_url(self, href, base_url):
        """Convert relative URL to absolute"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"https://docs.labellerr.com{href}"
        elif href.startswith('#'):
            return f"{base_url}{href}"
        else:
            return f"{base_url}/{href}"

    def extract_all_headings(self):
        """Main method to extract all headings from all pages"""
        print("🚀 Starting Documentation Headings Extraction...")
        
        # Get all documentation page URLs
        page_links = self.extract_page_links()
        print(f"📄 Found {len(page_links)} documentation pages")
        
        if not page_links:
            print("❌ No pages found!")
            return
        
        # Extract headings from each page
        for i, url in enumerate(page_links, 1):
            print(f"\n[{i}/{len(page_links)}] Processing page...")
            
            page_headings = self.extract_headings_from_page(url)
            self.all_headings.extend(page_headings)
            
            # Rate limiting
            time.sleep(2)
        
        # Save results
        self.save_headings()

    def save_headings(self):
        """Save extracted headings to JSON file"""
        if not self.all_headings:
            print("❌ No headings extracted!")
            return
        
        # Main headings file
        headings_file = os.path.join(self.output_dir, "labellerr_documentation_headings.json")
        with open(headings_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_headings, f, ensure_ascii=False, indent=2)
        
        # Create a simplified version with just heading and URL
        simplified_headings = [
            {
                "heading": h["heading"], 
                "url": h["url"],
                "level": h["level"]
            } 
            for h in self.all_headings
        ]
        
        simple_file = os.path.join(self.output_dir, "doc_headings_simple.json")
        with open(simple_file, 'w', encoding='utf-8') as f:
            json.dump(simplified_headings, f, ensure_ascii=False, indent=2)
        
        # Create summary
        summary = {
            "extraction_date": datetime.now().isoformat(),
            "total_headings": len(self.all_headings),
            "heading_levels": self.get_heading_level_breakdown(),
            "pages_processed": len(set(h["page_url"] for h in self.all_headings)),
            "sample_headings": self.all_headings[:10]  # First 10 as examples
        }
        
        summary_file = os.path.join(self.output_dir, "headings_extraction_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 Headings extraction completed!")
        print(f"📊 Results:")
        print(f"  • Total headings extracted: {len(self.all_headings)}")
        print(f"  • Pages processed: {summary['pages_processed']}")
        print(f"  • Heading levels: {summary['heading_levels']}")
        print(f"📁 Files saved:")
        print(f"  • Full data: {headings_file}")
        print(f"  • Simplified: {simple_file}")
        print(f"  • Summary: {summary_file}")

    def get_heading_level_breakdown(self):
        """Get breakdown of headings by level"""
        levels = {}
        for heading in self.all_headings:
            level = f"h{heading['level']}"
            levels[level] = levels.get(level, 0) + 1
        return levels

    def print_sample_headings(self, count=15):
        """Print sample headings for preview"""
        print(f"\n📋 Sample headings (first {count}):")
        for i, heading in enumerate(self.all_headings[:count], 1):
            level_indent = "  " * (heading['level'] - 1)
            print(f"{i:2}. {level_indent}[H{heading['level']}] {heading['heading']}")
            print(f"    URL: {heading['url']}")

def main():
    """Main execution"""
    print("🚀 Starting Labellerr Documentation Headings Extraction...")
    
    # Check ChromeDriver availability
    try:
        ChromeDriverManager().install()
        print("✅ ChromeDriver ready")
    except Exception as e:
        print(f"❌ ChromeDriver issue: {e}")
        return
    
    # Extract headings
    extractor = DocumentationHeadingsExtractor()
    extractor.extract_all_headings()
    
    # Show sample results
    if extractor.all_headings:
        extractor.print_sample_headings()

if __name__ == "__main__":
    main()
