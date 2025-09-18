from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import csv
from urllib.parse import urljoin, urlparse
import time

def scrape_links_selenium(url):
    """
    Scrape links using Selenium (handles JavaScript)
    """
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load the page
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Find all anchor elements
        link_elements = driver.find_elements(By.TAG_NAME, "a")
        
        links = []
        for element in link_elements:
            try:
                href = element.get_attribute("href")
                if href:
                    link_text = element.text.strip()
                    links.append({
                        'url': href,
                        'text': link_text,
                        'original_href': href
                    })
            except Exception as e:
                continue
        
        driver.quit()
        return links
    
    except Exception as e:
        print(f"Error with Selenium: {e}")
        return []
    

def save_links_to_csv(links, filename='scraped_links.csv'):
    """
    Save links to a CSV file
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['url', 'text', 'original_href']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for link in links:
            writer.writerow(link)


# Usage for Selenium method
if __name__ == "__main__":
    target_url = "https://www.labellerr.com/"
    
    print(f"Scraping links with Selenium from: {target_url}")
    scraped_links = scrape_links_selenium(target_url)
    
    if scraped_links:
        print(f"Found {len(scraped_links)} links")
        
        # Remove duplicates
        unique_links = []
        seen_urls = set()
        for link in scraped_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
        
        print(f"Unique links: {len(unique_links)}")
        
        # Save to CSV
        
        save_links_to_csv(unique_links, 'selenium_scraped_links.csv')
        print("Links saved to 'selenium_scraped_links.csv'")
