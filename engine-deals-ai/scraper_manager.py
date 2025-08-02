import logging
from typing import List, Dict
from scrapers.craigslist import CraigslistScraper
from scrapers.ebay import EbayScraper
from scrapers.facebook import FacebookScraper
from scrapers.offerup import OfferUpScraper

class ScraperManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.scrapers = {
            'craigslist': CraigslistScraper(config),
            'ebay': EbayScraper(config),
            'facebook': FacebookScraper(config),
            'offerup': OfferUpScraper(config)
        }
    
    def scrape_all_platforms(self) -> List[Dict]:
        """Scrape all platforms and return combined results"""
        all_listings = []
        
        for platform_name, scraper in self.scrapers.items():
            try:
                self.logger.info(f"Scraping {platform_name}...")
                listings = scraper.scrape_listings(
                    self.config.SEARCH_TERMS,
                    self.config.MAX_PAGES_PER_SITE
                )
                
                self.logger.info(f"Found {len(listings)} listings on {platform_name}")
                all_listings.extend(listings)
                
            except Exception as e:
                self.logger.error(f"Error scraping {platform_name}: {e}")
                continue
        
        self.logger.info(f"Total listings scraped: {len(all_listings)}")
        return all_listings
    
    def scrape_platform(self, platform_name: str) -> List[Dict]:
        """Scrape a specific platform"""
        if platform_name not in self.scrapers:
            raise ValueError(f"Unknown platform: {platform_name}")
        
        scraper = self.scrapers[platform_name]
        
        self.logger.info(f"Scraping {platform_name}...")
        listings = scraper.scrape_listings(
            self.config.SEARCH_TERMS,
            self.config.MAX_PAGES_PER_SITE
        )
        
        self.logger.info(f"Found {len(listings)} listings on {platform_name}")
        return listings
    
    def test_scrapers(self) -> Dict[str, bool]:
        """Test all scrapers with multiple search terms"""
        results = {}
        test_terms = ["Chevy V8 engine", "LS engine", "engine block"]  # Use broader terms that return real listings
        
        for platform_name, scraper in self.scrapers.items():
            try:
                self.logger.info(f"Testing {platform_name} scraper...")
                listings = scraper.scrape_listings(test_terms, max_pages=1)
                results[platform_name] = len(listings) > 0
                self.logger.info(f"{platform_name} test: {'PASS' if results[platform_name] else 'FAIL'} ({len(listings)} listings)")
            except Exception as e:
                self.logger.error(f"{platform_name} test failed: {e}")
                results[platform_name] = False
        
        return results
