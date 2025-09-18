import csv
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

def extract_content_selenium(url, driver):
    """
    Extract content using Selenium (handles JavaScript)
    """
    try:
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        content_data = {
            'url': url,
            'status': 'success',
            'title': driver.title,
            'meta_description': '',
            'headings': {
                'h1': [h.text.strip() for h in soup.find_all('h1')],
                'h2': [h.text.strip() for h in soup.find_all('h2')],
                'h3': [h.text.strip() for h in soup.find_all('h3')]
            },
            'paragraphs': [p.text.strip() for p in soup.find_all('p') if p.text.strip()],
            'links': [{'text': a.text.strip(), 'href': a.get('href')} for a in soup.find_all('a', href=True)],
            'images': [{'alt': img.get('alt', ''), 'src': img.get('src', '')} for img in soup.find_all('img')],
            'text_content': soup.get_text(separator=' ', strip=True),
            'word_count': len(soup.get_text().split()),
            'page_height': driver.execute_script("return document.body.scrollHeight"),
            'loaded_with_js': True
        }
        
        # Extract meta description
        try:
            meta_desc = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
            content_data['meta_description'] = meta_desc.get_attribute('content')
        except:
            pass
        
        return content_data
        
    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        return {
            'url': url,
            'status': 'error',
            'error': str(e),
            'loaded_with_js': True
        }

def process_urls_selenium(csv_file, output_json_file):
    """
    Process URLs using Selenium
    """
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Read URLs from CSV
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            urls = [row['url'] for row in reader]
        
        all_content = []
        
        for i, url in enumerate(urls, 1):
            logging.info(f"Processing {i}/{len(urls)}: {url}")
            content = extract_content_selenium(url, driver)
            all_content.append(content)
            
            # Save progress every 5 URLs
            if i % 5 == 0:
                with open(f"temp_selenium_{output_json_file}", 'w', encoding='utf-8') as f:
                    json.dump(all_content, f, ensure_ascii=False, indent=2)
        
        # Save final results
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(all_content, f, ensure_ascii=False, indent=2)
        
        driver.quit()
        logging.info(f"Selenium processing completed. Results saved to {output_json_file}")
        
        return all_content
        
    except Exception as e:
        logging.error(f"Error in selenium processing: {e}")
        return None

# Usage for Selenium method
if __name__ == "__main__":
    csv_file = 'selenium_scraped_links.csv'
    output_file = 'selenium_extracted_content.json'
    
    results = process_urls_selenium(csv_file, output_file)
