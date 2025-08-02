#!/usr/bin/env python3
"""
Debug script to examine eBay HTML structure in detail
"""

import requests
from bs4 import BeautifulSoup

def debug_ebay_html():
    print("=== EBAY HTML STRUCTURE DEBUG ===")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    try:
        response = session.get('https://www.ebay.com/sch/i.html?_nkw=Chevy+V8+engine', timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('li', class_='s-item')
        
        print(f"Found {len(items)} items")
        
        if items:
            for i, item in enumerate(items[:10]):
                print(f"\n--- ITEM {i+1} ---")
                
                all_links = item.find_all('a', href=True)
                print(f"Total links in item: {len(all_links)}")
                
                for j, link in enumerate(all_links):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    classes = link.get('class', [])
                    
                    print(f"  Link {j+1}:")
                    print(f"    Classes: {classes}")
                    print(f"    Text: {text[:60]}...")
                    print(f"    URL: {href[:80]}...")
                    
                    if ('itm' in href or 'item' in href) and len(text) > 10:
                        print(f"    *** POTENTIAL LISTING LINK ***")
                
                price_spans = item.find_all('span', class_=lambda x: x and 'price' in ' '.join(x).lower())
                print(f"Price elements found: {len(price_spans)}")
                for price_span in price_spans[:2]:
                    print(f"  Price: {price_span.get('class', [])} -> {price_span.get_text(strip=True)}")
                
                title_elements = item.find_all(['h3', 'span', 'a'], class_=lambda x: x and any(word in ' '.join(x).lower() for word in ['title', 'name']))
                print(f"Title elements found: {len(title_elements)}")
                for title_elem in title_elements[:2]:
                    print(f"  Title: {title_elem.get('class', [])} -> {title_elem.get_text(strip=True)[:50]}...")
        
        with open('ebay_html_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\nHTML saved to ebay_html_debug.html")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ebay_html()
