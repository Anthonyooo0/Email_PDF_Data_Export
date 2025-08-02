#!/usr/bin/env python3
"""
Debug script to examine eBay HTML structure
"""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def debug_ebay_structure():
    """Debug the actual HTML structure of eBay search results"""
    
    session = requests.Session()
    ua = UserAgent()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    base_url = "https://www.ebay.com"
    search_url = f"{base_url}/sch/i.html"
    params = {
        '_nkw': 'engine',
        '_pgn': 1,
        '_sop': 10,  # Sort by newly listed
        'LH_ItemCondition': '3000|1500|2500',  # Used, New other, Seller refurbished
        '_udlo': 50,  # Min price $50
        '_udhi': 10000,  # Max price $10,000
    }
    
    try:
        print(f"Testing URL: {search_url}")
        print(f"Params: {params}")
        
        response = session.get(search_url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            with open('/home/ubuntu/engine-deals-ai/ebay_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            print("\n=== DEBUGGING HTML STRUCTURE ===")
            
            possible_selectors = [
                ('div.s-item__wrapper', soup.find_all('div', class_='s-item__wrapper')),
                ('div.s-item', soup.find_all('div', class_='s-item')),
                ('li.s-item', soup.find_all('li', class_='s-item')),
                ('div.srp-results', soup.find_all('div', class_='srp-results')),
                ('div[class*="item"]', soup.find_all('div', class_=lambda x: x and 'item' in x)),
            ]
            
            for selector_name, elements in possible_selectors:
                print(f"\n{selector_name}: Found {len(elements)} elements")
                if elements:
                    print(f"  First element classes: {elements[0].get('class', [])}")
                    print(f"  First element preview: {str(elements[0])[:200]}...")
            
            title_selectors = [
                ('h3.s-item__title', soup.find_all('h3', class_='s-item__title')),
                ('a.s-item__link', soup.find_all('a', class_='s-item__link')),
                ('span.s-item__title--tag', soup.find_all('span', class_='s-item__title--tag')),
                ('a[href*="/itm/"]', soup.find_all('a', href=lambda x: x and '/itm/' in x)),
            ]
            
            print("\n=== TITLE LINK ANALYSIS ===")
            for selector_name, elements in title_selectors:
                print(f"{selector_name}: Found {len(elements)} elements")
                if elements:
                    print(f"  First title: {elements[0].get_text(strip=True)[:50]}...")
                    if elements[0].name == 'a':
                        print(f"  First href: {elements[0].get('href', 'No href')}")
            
            all_links = soup.find_all('a', href=True)
            listing_links = [link for link in all_links if '/itm/' in link.get('href', '')]
            print(f"\nTotal links with /itm/: {len(listing_links)}")
            
            if listing_links:
                print("Sample listing links:")
                for i, link in enumerate(listing_links[:3]):
                    print(f"  {i+1}. {link.get_text(strip=True)[:50]} -> {link.get('href')}")
            
            if 'blocked' in response.text.lower() or 'captcha' in response.text.lower():
                print("\n⚠️  WARNING: Possible blocking or CAPTCHA detected")
            
            if 'no results' in response.text.lower() or 'try again' in response.text.lower():
                print(f"\n⚠️  Possible error messages detected")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_ebay_structure()
