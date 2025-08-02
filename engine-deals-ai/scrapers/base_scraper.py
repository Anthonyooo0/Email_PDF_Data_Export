import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
import requests
from bs4 import BeautifulSoup

class BaseScraper(ABC):
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self.setup_session()
    
    def setup_session(self):
        """Setup requests session with headers"""
        ua = UserAgent()
        self.session.headers.update({
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def get_selenium_driver(self, headless: bool = True) -> webdriver.Chrome:
        """Create a Selenium Chrome driver"""
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        ua = UserAgent()
        options.add_argument(f'--user-agent={ua.random}')
        
        driver = webdriver.Chrome(options=options)
        return driver
    
    def random_delay(self):
        """Add random delay between requests"""
        delay = random.uniform(*self.config.REQUEST_DELAY)
        time.sleep(delay)
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        import re
        price_clean = re.sub(r'[^\d.,]', '', price_text.replace(',', ''))
        
        try:
            return float(price_clean)
        except (ValueError, TypeError):
            return None
    
    def extract_condition_keywords(self, text: str) -> List[str]:
        """Extract condition-related keywords from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.config.GOOD_CONDITION_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(f"good_{keyword}")
        
        for keyword in self.config.BAD_CONDITION_KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(f"bad_{keyword}")
        
        return found_keywords
    
    def is_relevant_listing(self, title: str, description: str = "") -> bool:
        """Check if listing is relevant to our search"""
        text = f"{title} {description}".lower()
        
        engine_terms = ["engine", "motor", "block", "head", "intake", "crank", "piston", "long block", "short block"]
        has_engine_term = any(term in text for term in engine_terms)
        
        if has_engine_term:
            exclude_terms = ["boat", "marine", "motorcycle", "lawn", "generator", "pump", "compressor"]
            has_exclude_term = any(term in text for term in exclude_terms)
            
            if not has_exclude_term:
                return True
        
        return False
    
    @abstractmethod
    def scrape_listings(self, search_terms: List[str], max_pages: int = 5) -> List[Dict]:
        """Scrape listings from the platform"""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the platform name"""
        pass
