#!/usr/bin/env python3
"""
Detailed debug script to compare debug vs scraper behavior
"""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import urllib.parse

def test_ebay_detailed():
    print("=== DETAILED EBAY DEBUG ===")
    
    session = requests.Session()
    ua = UserAgent()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    
    search_url = "https://www.ebay.com/sch/i.html"
    search_term = "LQ4 engine"
    
    params = {
        '_nkw': search_term,
        '_pgn': 1,
        '_sop': 10,  # Sort by newly listed
        'LH_ItemCondition': '3000|1500|2500',  # Used, New other, Seller refurbished
        '_udlo': 50,  # Min price $50
        '_udhi': 10000,  # Max price $10,000
    }
    
    print(f"Testing URL: {search_url}")
    print(f"Params: {params}")
    print(f"User-Agent: {session.headers['User-Agent']}")
    
    try:
        response = session.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        items = soup.find_all('li', class_='s-item')
        print(f"\nFound {len(items)} li.s-item elements")
        
        if items:
            print(f"First item classes: {items[0].get('class', [])}")
            
            for i, item in enumerate(items[:3]):
                print(f"\n--- Item {i+1} ---")
                print(f"Item classes: {item.get('class', [])}")
                
                title_link = item.find('a', class_='s-item__link')
                if title_link:
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href', '')
                    print(f"✓ Found title link: {title[:50]}...")
                    print(f"  URL: {url[:100]}...")
                else:
                    print("✗ No title link found")
                    all_links = item.find_all('a', href=True)
                    print(f"  Found {len(all_links)} total links in item")
                    for j, link in enumerate(all_links[:2]):
                        print(f"    Link {j+1}: {link.get('class', [])} -> {link.get('href', '')[:50]}...")
        
        with open('ebay_scraper_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\nHTML saved to ebay_scraper_debug.html")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ebay_detailed()
