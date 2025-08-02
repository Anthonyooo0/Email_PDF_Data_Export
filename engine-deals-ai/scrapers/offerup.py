import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import urllib.parse
from .base_scraper import BaseScraper

class OfferUpScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://offerup.com"
    
    def get_platform_name(self) -> str:
        return "offerup"
    
    def scrape_listings(self, search_terms: List[str], max_pages: int = 5) -> List[Dict]:
        """Scrape OfferUp listings"""
        all_listings = []
        
        for search_term in search_terms:
            try:
                listings = self._scrape_search_results(search_term, max_pages)
                all_listings.extend(listings)
                self.random_delay()
            except Exception as e:
                self.logger.error(f"Error scraping OfferUp for '{search_term}': {e}")
        
        return all_listings
    
    def _scrape_search_results(self, search_term: str, max_pages: int) -> List[Dict]:
        """Scrape search results for a specific term"""
        listings = []
        
        search_url = f"{self.base_url}/search/"
        
        for page in range(1, max_pages + 1):
            params = {
                'q': search_term,
                'page': page,
                'sort': 'date'
            }
            
            try:
                response = self.session.get(search_url, params=params, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                items = soup.find_all('div', {'data-testid': 'item-card'}) or \
                       soup.find_all('a', href=lambda x: x and '/item/' in x)
                
                if not items:
                    items = soup.find_all('div', class_=lambda x: x and 'item' in x.lower())
                
                if not items:
                    break
                
                for item in items:
                    listing = self._parse_listing_item(item)
                    if listing and self.is_relevant_listing(listing['title'], listing.get('description', '')):
                        listings.append(listing)
                
                self.random_delay()
                
            except Exception as e:
                self.logger.error(f"Error scraping OfferUp page {page} for {search_term}: {e}")
                break
        
        return listings
    
    def _parse_listing_item(self, item) -> Dict:
        """Parse individual OfferUp listing item"""
        try:
            title_elem = item.find('h2') or item.find('span', class_=lambda x: x and 'title' in x.lower())
            if not title_elem:
                link_elem = item if item.name == 'a' else item.find('a')
                if link_elem and link_elem.get('href'):
                    title = link_elem.get('title', '') or link_elem.get_text(strip=True)
                    url = link_elem['href']
                else:
                    return None
            else:
                title = title_elem.get_text(strip=True)
                link_elem = item.find('a') or title_elem.find_parent('a')
                url = link_elem['href'] if link_elem else ""
            
            if not url.startswith('http'):
                url = self.base_url + url
            
            price_elem = item.find('span', class_=lambda x: x and 'price' in x.lower()) or \
                        item.find('span', string=lambda x: x and '$' in x)
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self.extract_price(price_text)
            
            location_elem = item.find('span', class_=lambda x: x and 'location' in x.lower())
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            img_elem = item.find('img')
            image_urls = [img_elem['src']] if img_elem and img_elem.get('src') else []
            
            condition_keywords = self.extract_condition_keywords(title)
            
            listing = {
                'platform': self.get_platform_name(),
                'title': title,
                'url': url,
                'price': price,
                'location': location,
                'seller_name': "OfferUp User",
                'description': "",
                'image_urls': image_urls,
                'condition_keywords': condition_keywords
            }
            
            return listing
            
        except Exception as e:
            self.logger.error(f"Error parsing OfferUp listing: {e}")
            return None
    
    def _get_listing_details(self, url: str) -> Dict:
        """Get detailed information from OfferUp listing page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            description_elem = soup.find('div', class_=lambda x: x and 'description' in x.lower()) or \
                             soup.find('p', class_=lambda x: x and 'description' in x.lower())
            description = description_elem.get_text(strip=True) if description_elem else ""
            
            seller_elem = soup.find('span', class_=lambda x: x and 'seller' in x.lower()) or \
                         soup.find('div', class_=lambda x: x and 'seller' in x.lower())
            seller_name = seller_elem.get_text(strip=True) if seller_elem else "OfferUp User"
            
            return {
                'description': description,
                'seller_name': seller_name
            }
            
        except Exception as e:
            self.logger.error(f"Error getting OfferUp listing details: {e}")
            return {'description': '', 'seller_name': 'OfferUp User'}
