#!/usr/bin/env python3
"""
Kome.ai YouTube Transcript Extractor using Playwright - FIXED VERSION
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

INPUT_JSON = "data_ingest/raw/youtube/failed_transcripts.json"
OUTPUT_JSON = "kome_transcripts.json"

async def extract_video_entries(json_file):
    """Extract YouTube URLs from JSON file error messages - FIXED"""
    data = json.loads(Path(json_file).read_text(encoding="utf-8"))
    entries = []
    
    for item in data:
        urls = re.findall(r'https?://[^\s!]+', item.get("error", ""))
        for url in urls:
            if "youtube.com/watch" in url or "youtu.be/" in url:
                entries.append({
                    "video_id": item.get("video_id", ""),
                    "title": item.get("title", ""),
                    "url": url.rstrip("!"),
                    "original_error": item.get("error", "")  # Fixed key
                })
    return entries

async def fetch_kome_transcript(page, video_url, max_retries=2):
    """Fetch transcript from Kome.ai"""
    
    for attempt in range(max_retries):
        try:
            print(f"  🔄 Attempt {attempt + 1}/{max_retries}")
            
            await page.goto("https://kome.ai/tools/youtube-transcript-generator", 
                          wait_until="networkidle", timeout=30000)
            
            await page.wait_for_selector('input[type="url"]', timeout=20000)
            await page.fill('input[type="url"]', video_url)
            await page.click('button[type="submit"]')
            print("  ✅ Form submitted")
            
            # Wait and look for transcript
            await page.wait_for_timeout(5000)
            
            # Try multiple selectors for transcript content
            selectors = [
                '[class*="transcript"]',
                '[class*="result"]', 
                '[class*="output"]',
                '[class*="content"]',
                'pre',
                'textarea[readonly]'
            ]
            
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        text = await element.text_content()
                        if text and len(text.strip()) > 100:
                            print(f"  ✅ Found transcript with: {selector}")
                            return text.strip()
                except:
                    continue
            
            # Extended wait and broader search
            await page.wait_for_timeout(15000)
            
            all_elements = await page.query_selector_all('div, p, span, section')
            for element in all_elements:
                try:
                    text = await element.text_content()
                    if text and len(text.strip()) > 200:
                        if not any(word in text.lower() for word in ['navigation', 'footer', 'header', 'menu']):
                            print("  ✅ Found transcript via text scan")
                            return text.strip()
                except:
                    continue
            
            print(f"  ❌ Attempt {attempt + 1} failed")
            
        except Exception as e:
            print(f"  ❌ Attempt {attempt + 1} error: {str(e)[:100]}...")
        
        if attempt < max_retries - 1:
            await page.wait_for_timeout(3000)
    
    return None

async def main():
    """Main function"""
    
    if not Path(INPUT_JSON).exists():
        print(f"❌ Input file '{INPUT_JSON}' not found!")
        return
    
    print("🚀 Starting Kome.ai transcript extraction...")
    
    entries = await extract_video_entries(INPUT_JSON)
    print(f"📋 Found {len(entries)} videos to process")
    
    results = []
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        for i, entry in enumerate(entries, start=1):
            print(f"\n[{i}/{len(entries)}] Processing: {entry['title'][:60]}...")
            
            try:
                transcript = await fetch_kome_transcript(page, entry["url"])
                
                if transcript and len(transcript) > 50:
                    status = "success"
                    print(f"  ✅ Success! Length: {len(transcript)} characters")
                else:
                    status = "failed"
                    transcript = ""
                    print("  ❌ Failed to get transcript")
                
            except Exception as e:
                transcript = ""
                status = "failed"
                print(f"  ❌ Error: {str(e)[:100]}...")
            
            results.append({
                "video_id": entry["video_id"],
                "title": entry["title"],
                "url": entry["url"],
                "transcript_status": status,
                "transcript": transcript,
                "source": "kome_playwright",
                "original_error": entry["original_error"]
            })
            
            await page.wait_for_timeout(5000)
        
        await browser.close()
    
    # Save results
    Path(OUTPUT_JSON).write_text(
        json.dumps(results, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )
    
    # Summary
    successful = sum(1 for r in results if r['transcript_status'] == 'success')
    print(f"\n📊 Summary:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {len(results) - successful}")
    print(f"📁 Results saved to: {OUTPUT_JSON}")

if __name__ == "__main__":
    asyncio.run(main())
