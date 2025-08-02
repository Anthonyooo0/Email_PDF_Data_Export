import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse
from .base_scraper import BaseScraper

class EbayScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.ebay.com"
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_platform_name(self) -> str:
        return "ebay"
    
    def scrape_listings(self, search_terms: List[str], max_pages: int = 5) -> List[Dict]:
        """Scrape eBay listings"""
        all_listings = []
        
        for search_term in search_terms:
            try:
                listings = self._scrape_search_results(search_term, max_pages)
                all_listings.extend(listings)
                self.random_delay()
            except Exception as e:
                self.logger.error(f"Error scraping eBay for '{search_term}': {e}")
        
        return all_listings
    
    def _scrape_search_results(self, search_term: str, max_pages: int) -> List[Dict]:
        """Scrape search results for a specific term"""
        listings = []
        
        search_url = f"{self.base_url}/sch/i.html"
        
        for page in range(1, max_pages + 1):
            params = {
                '_nkw': search_term,
                '_pgn': page,
                '_sop': 10,  # Sort by newly listed
                'LH_ItemCondition': '3000|1500|2500',  # Used, New other, Seller refurbished
                '_udlo': 50,  # Min price $50
                '_udhi': 10000,  # Max price $10,000
            }
            
            try:
                response = self.session.get(search_url, params=params, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                items = soup.find_all('li', class_='s-item')
                
                self.logger.info(f"Found {len(items)} items on page {page}")
                
                if not items:
                    break
                
                for item in items:
                    listing = self._parse_listing_item(item)
                    if listing:
                        self.logger.info(f"Parsed listing: {listing['title'][:50]}... - ${listing['price']}")
                        if self.is_relevant_listing(listing['title'], listing.get('description', '')):
                            listings.append(listing)
                        else:
                            self.logger.info(f"Listing not relevant: {listing['title'][:50]}...")
                    else:
                        self.logger.warning(f"Failed to parse listing item: {item.get('class', [])} - {str(item)[:100]}...")
                
                self.random_delay()
                
            except Exception as e:
                self.logger.error(f"Error scraping eBay page {page} for {search_term}: {e}")
                break
        
        return listings
    
    def _parse_listing_item(self, item) -> Dict:
        """Parse individual eBay listing item"""
        try:
            title_link = item.find('a', class_='s-item__link')
            if not title_link:
                self.logger.warning(f"No title link found in item: {item.get('class', [])}")
                return None
            
            title = title_link.get_text(strip=True)
            url = title_link.get('href', '')
            
            if not url:
                self.logger.warning(f"No URL found for title: {title}")
                return None
            
            if ('SPONSORED' in title.upper() or 
                'Shop on eBay' in title or 
                'Opens in a new window' in title or
                not url.startswith('https://www.ebay.com/itm/') or
                'itmmeta=' in url):
                self.logger.debug(f"Skipping promotional/sponsored item: {title[:50]}...")
                return None
            
            price_elem = item.find('span', class_='s-item__price')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self.extract_price(price_text)
            
            location_elem = item.find('span', class_='s-item__location')
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            seller_elem = item.find('span', class_='s-item__seller-info-text')
            seller_name = seller_elem.get_text(strip=True) if seller_elem else "Unknown"
            
            condition_elem = item.find('span', class_='SECONDARY_INFO')
            condition_text = condition_elem.get_text(strip=True) if condition_elem else ""
            
            img_elem = item.find('img', class_='s-item__image')
            image_urls = [img_elem['src']] if img_elem and img_elem.get('src') else []
            
            condition_keywords = self.extract_condition_keywords(f"{title} {condition_text}")
            
            listing = {
                'platform': self.get_platform_name(),
                'title': title,
                'url': url,
                'price': price,
                'location': location,
                'seller_name': seller_name,
                'description': condition_text,
                'image_urls': image_urls,
                'condition_keywords': condition_keywords
            }
            
            return listing
            
        except Exception as e:
            self.logger.error(f"Error parsing eBay listing: {e}")
            return None
