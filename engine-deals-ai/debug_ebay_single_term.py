#!/usr/bin/env python3
"""
Debug script to test eBay scraper with single term like the comprehensive test
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from scrapers.ebay import EbayScraper

def test_ebay_single_term():
    print("=== EBAY SINGLE TERM DEBUG ===")
    
    config = Config()
    scraper = EbayScraper(config)
    
    test_terms = ["LQ4 engine", "Chevy V8 engine", "LS engine"]
    max_pages = 1
    
    print(f"Testing eBay scraper with:")
    print(f"  Search terms: {test_terms}")
    print(f"  Max pages: {max_pages}")
    print(f"  User-Agent: {scraper.session.headers.get('User-Agent', 'Not set')}")
    
    try:
        listings = scraper.scrape_listings(test_terms, max_pages=max_pages)
        print(f"\nResult: Found {len(listings)} listings")
        
        if listings:
            print("\nFirst 3 listings:")
            for i, listing in enumerate(listings[:3]):
                print(f"  {i+1}. {listing.get('title', 'No title')[:60]}... - ${listing.get('price', 'N/A')}")
        else:
            print("No listings found - investigating...")
            
            search_url = "https://www.ebay.com/sch/i.html"
            params = {
                '_nkw': test_terms[0],  # Use first search term
                '_pgn': 1,
                '_sop': 10,
                'LH_ItemCondition': '3000|1500|2500',
                '_udlo': 50,
                '_udhi': 10000,
            }
            
            response = scraper.session.get(search_url, params=params, timeout=15)
            print(f"Raw request status: {response.status_code}")
            print(f"Raw request URL: {response.url}")
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('li', class_='s-item')
            print(f"Raw HTML items found: {len(items)}")
            
            if items:
                print("First item analysis:")
                item = items[0]
                print(f"  Item classes: {item.get('class', [])}")
                
                title_link = item.find('a', class_='s-item__link')
                print(f"  Title link found: {title_link is not None}")
                if title_link:
                    print(f"  Title: {title_link.get_text(strip=True)[:50]}...")
                    print(f"  URL: {title_link.get('href', 'No href')[:50]}...")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ebay_single_term()
