#!/usr/bin/env python3
"""
Debug script to analyze eBay HTML structure and fix parsing issues
"""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def debug_ebay_parsing():
    print("=== EBAY PARSING DEBUG ===")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    search_url = "https://www.ebay.com/sch/i.html"
    params = {
        '_nkw': 'Chevy V8 engine',
        '_pgn': 1,
        '_sop': 10,
        'LH_ItemCondition': '3000|1500|2500',
        '_udlo': 50,
        '_udhi': 10000,
    }
    
    try:
        response = session.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('li', class_='s-item')
        
        print(f"Found {len(items)} items")
        
        if items:
            for i, item in enumerate(items[:3]):
                print(f"\n--- ITEM {i+1} ---")
                print(f"Classes: {item.get('class', [])}")
                
                title_link = item.find('a', class_='s-item__link')
                print(f"Title link found: {title_link is not None}")
                
                if title_link:
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href', '')
                    print(f"Title: {title}")
                    print(f"URL: {url}")
                    print(f"URL starts with ebay.com/itm/: {url.startswith('https://www.ebay.com/itm/')}")
                    print(f"Contains itmmeta: {'itmmeta=' in url}")
                else:
                    all_links = item.find_all('a', href=True)
                    print(f"Found {len(all_links)} total links")
                    for j, link in enumerate(all_links[:2]):
                        print(f"  Link {j+1}: {link.get('class', [])} -> {link.get('href', '')[:50]}...")
                
                price_elem = item.find('span', class_='s-item__price')
                print(f"Price element found: {price_elem is not None}")
                if price_elem:
                    print(f"Price text: {price_elem.get_text(strip=True)}")
                
                location_elem = item.find('span', class_='s-item__location')
                print(f"Location element found: {location_elem is not None}")
                if location_elem:
                    print(f"Location text: {location_elem.get_text(strip=True)}")
                
                seller_elem = item.find('span', class_='s-item__seller-info-text')
                print(f"Seller element found: {seller_elem is not None}")
                if seller_elem:
                    print(f"Seller text: {seller_elem.get_text(strip=True)}")
                
                condition_elem = item.find('span', class_='SECONDARY_INFO')
                print(f"Condition element found: {condition_elem is not None}")
                if condition_elem:
                    print(f"Condition text: {condition_elem.get_text(strip=True)}")
                
                img_elem = item.find('img', class_='s-item__image')
                print(f"Image element found: {img_elem is not None}")
                if img_elem:
                    print(f"Image src: {img_elem.get('src', '')[:50]}...")
        
        with open('ebay_parsing_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\nHTML saved to ebay_parsing_debug.html")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ebay_parsing()
