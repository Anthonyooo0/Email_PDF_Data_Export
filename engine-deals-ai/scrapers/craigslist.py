import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse
import time
import random
from .base_scraper import BaseScraper

class CraigslistScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_urls = [
            "https://newyork.craigslist.org",
            "https://losangeles.craigslist.org", 
            "https://chicago.craigslist.org",
            "https://houston.craigslist.org",
            "https://phoenix.craigslist.org"
        ]
    
    def get_platform_name(self) -> str:
        return "craigslist"
    
    def scrape_listings(self, search_terms: List[str], max_pages: int = 5) -> List[Dict]:
        """Scrape Craigslist listings"""
        all_listings = []
        
        for base_url in self.base_urls:
            for search_term in search_terms:
                try:
                    listings = self._scrape_search_results(base_url, search_term, max_pages)
                    all_listings.extend(listings)
                    self.random_delay()
                except Exception as e:
                    self.logger.error(f"Error scraping {base_url} for '{search_term}': {e}")
        
        return all_listings
    
    def _scrape_search_results(self, base_url: str, search_term: str, max_pages: int) -> List[Dict]:
        """Scrape search results for a specific term"""
        listings = []
        
        search_url = f"{base_url}/search/pts"
        params = {
            'query': search_term,
            'sort': 'date'
        }
        
        max_pages = min(max_pages, 2)
        
        for page in range(max_pages):
            if page > 0:
                params['s'] = page * 120  # Craigslist shows 120 results per page
            
            try:
                if page > 0:
                    time.sleep(random.uniform(3, 7))
                
                response = self.session.get(search_url, params=params, timeout=15)
                
                if response.status_code == 403:
                    self.logger.warning(f"Got 403 Forbidden for {search_term} on {base_url} - skipping")
                    break
                
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                result_rows = soup.find_all('li', class_='cl-static-search-result')
                
                if not result_rows:
                    self.logger.warning(f"No results found on page {page} for {search_term}")
                    break
                
                for row in result_rows:
                    listing = self._parse_listing_row(row, base_url)
                    if listing and self.is_relevant_listing(listing['title'], listing.get('description', '')):
                        listings.append(listing)
                
                self.random_delay()
                
            except Exception as e:
                self.logger.error(f"Error scraping page {page} for {search_term}: {e}")
                break
        
        return listings
    
    def _parse_listing_row(self, row, base_url: str) -> Dict:
        """Parse individual listing row"""
        try:
            title_elem = row.find('a', href=True)
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get('href', '')
            if not url.startswith('http'):
                url = base_url + url
            
            price_text = title
            price = self.extract_price(price_text)
            
            location = ""
            parts = title.split('$')
            if len(parts) > 1:
                after_price = parts[-1]
                import re
                location_match = re.search(r'([A-Za-z\s]+)$', after_price)
                if location_match:
                    location = location_match.group(1).strip()
            
            detailed_info = self._get_listing_details(url)
            
            listing = {
                'platform': self.get_platform_name(),
                'title': title,
                'url': url,
                'price': price,
                'location': location,
                **detailed_info
            }
            
            return listing
            
        except Exception as e:
            self.logger.error(f"Error parsing listing row: {e}")
            return None
    
    def _get_listing_details(self, url: str) -> Dict:
        """Get detailed information from listing page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            description_elem = soup.find('section', id='postingbody')
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            image_urls = []
            image_container = soup.find('div', class_='gallery')
            if image_container:
                img_tags = image_container.find_all('img')
                image_urls = [img.get('src') for img in img_tags if img.get('src')]
            
            seller_name = "Anonymous"
            
            condition_keywords = self.extract_condition_keywords(f"{description}")
            
            return {
                'description': description,
                'image_urls': image_urls,
                'seller_name': seller_name,
                'condition_keywords': condition_keywords
            }
            
        except Exception as e:
            self.logger.error(f"Error getting listing details from {url}: {e}")
            return {
                'description': "",
                'image_urls': [],
                'seller_name': "Unknown",
                'condition_keywords': []
            }
