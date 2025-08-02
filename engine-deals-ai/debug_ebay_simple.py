#!/usr/bin/env python3
"""
Simple eBay debug script to test different search approaches
"""

import requests
from bs4 import BeautifulSoup
import time

def test_ebay_simple():
    print("=== SIMPLE EBAY DEBUG ===")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    })
    
    test_cases = [
        {
            'name': 'Simple search - no filters',
            'url': 'https://www.ebay.com/sch/i.html',
            'params': {'_nkw': 'Chevy V8 engine'}
        },
        {
            'name': 'With basic filters',
            'url': 'https://www.ebay.com/sch/i.html',
            'params': {
                '_nkw': 'Chevy V8 engine',
                '_sop': 10,
                '_udlo': 100,
                '_udhi': 5000,
            }
        },
        {
            'name': 'Different search term',
            'url': 'https://www.ebay.com/sch/i.html',
            'params': {'_nkw': 'engine block'}
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n--- TEST {i+1}: {test_case['name']} ---")
        
        try:
            response = session.get(test_case['url'], params=test_case['params'], timeout=20)
            response.raise_for_status()
            
            print(f"Status: {response.status_code}")
            print(f"URL: {response.url}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.find_all('li', class_='s-item')
            print(f"Items found: {len(items)}")
            
            if items:
                real_listings = 0
                for j, item in enumerate(items[:5]):
                    title_link = item.find('a', class_='s-item__link')
                    if title_link:
                        title = title_link.get_text(strip=True)
                        url = title_link.get('href', '')
                        
                        is_real = (not any(x in title for x in ['Shop on eBay', 'Opens in a new window']) and
                                  url.startswith('https://www.ebay.com/itm/') and
                                  'itmmeta=' not in url)
                        
                        if is_real:
                            real_listings += 1
                            print(f"  ✓ Real listing {real_listings}: {title[:60]}...")
                        else:
                            print(f"  ✗ Promotional: {title[:60]}...")
                
                print(f"Real listings found: {real_listings}/{len(items)}")
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_ebay_simple()
