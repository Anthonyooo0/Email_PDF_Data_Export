#!/usr/bin/env python3
"""
Debug script to examine Craigslist HTML structure
"""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def debug_craigslist_structure():
    """Debug the actual HTML structure of Craigslist search results"""
    
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
    
    base_url = "https://newyork.craigslist.org"
    search_url = f"{base_url}/search/pts"
    params = {
        'query': 'engine',
        'sort': 'date'
    }
    
    try:
        print(f"Testing URL: {search_url}")
        print(f"Params: {params}")
        
        response = session.get(search_url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            with open('/home/ubuntu/engine-deals-ai/craigslist_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            
            print("\n=== DEBUGGING HTML STRUCTURE ===")
            
            possible_selectors = [
                ('li.cl-search-result', soup.find_all('li', class_='cl-search-result')),
                ('li.result-row', soup.find_all('li', class_='result-row')),
                ('div.result-info', soup.find_all('div', class_='result-info')),
                ('li.cl-static-search-result', soup.find_all('li', class_='cl-static-search-result')),
                ('div.cl-search-result', soup.find_all('div', class_='cl-search-result')),
                ('li[class*="result"]', soup.find_all('li', class_=lambda x: x and 'result' in x)),
                ('div[class*="search"]', soup.find_all('div', class_=lambda x: x and 'search' in x)),
            ]
            
            for selector_name, elements in possible_selectors:
                print(f"\n{selector_name}: Found {len(elements)} elements")
                if elements:
                    print(f"  First element classes: {elements[0].get('class', [])}")
                    print(f"  First element preview: {str(elements[0])[:200]}...")
            
            title_selectors = [
                ('a.cl-app-anchor', soup.find_all('a', class_='cl-app-anchor')),
                ('a.result-title', soup.find_all('a', class_='result-title')),
                ('a[class*="title"]', soup.find_all('a', class_=lambda x: x and 'title' in x)),
                ('a[href*="/pts/"]', soup.find_all('a', href=lambda x: x and '/pts/' in x)),
            ]
            
            print("\n=== TITLE LINK ANALYSIS ===")
            for selector_name, elements in title_selectors:
                print(f"{selector_name}: Found {len(elements)} elements")
                if elements:
                    print(f"  First title: {elements[0].get_text(strip=True)[:50]}...")
                    print(f"  First href: {elements[0].get('href', 'No href')}")
            
            all_links = soup.find_all('a', href=True)
            listing_links = [link for link in all_links if '/pts/' in link.get('href', '')]
            print(f"\nTotal links with /pts/: {len(listing_links)}")
            
            if listing_links:
                print("Sample listing links:")
                for i, link in enumerate(listing_links[:3]):
                    print(f"  {i+1}. {link.get_text(strip=True)[:50]} -> {link.get('href')}")
            
            if 'blocked' in response.text.lower() or 'captcha' in response.text.lower():
                print("\n⚠️  WARNING: Possible blocking or CAPTCHA detected")
            
            error_indicators = soup.find_all(text=lambda text: text and any(
                phrase in text.lower() for phrase in ['no results', 'try again', 'error', 'blocked']
            ))
            if error_indicators:
                print(f"\n⚠️  Possible error messages found: {error_indicators[:3]}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_craigslist_structure()
