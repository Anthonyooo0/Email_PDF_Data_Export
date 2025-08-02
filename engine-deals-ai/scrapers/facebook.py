from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import List, Dict
import time
from .base_scraper import BaseScraper

class FacebookScraper(BaseScraper):
    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://www.facebook.com/marketplace"
    
    def get_platform_name(self) -> str:
        return "facebook"
    
    def scrape_listings(self, search_terms: List[str], max_pages: int = 5) -> List[Dict]:
        """Scrape Facebook Marketplace listings using Selenium"""
        all_listings = []
        driver = None
        
        try:
            driver = self.get_selenium_driver(headless=True)
            
            for search_term in search_terms:
                try:
                    listings = self._scrape_search_results(driver, search_term, max_pages)
                    all_listings.extend(listings)
                    time.sleep(3)  # Longer delay for Facebook
                except Exception as e:
                    self.logger.error(f"Error scraping Facebook for '{search_term}': {e}")
            
        finally:
            if driver:
                driver.quit()
        
        return all_listings
    
    def _scrape_search_results(self, driver, search_term: str, max_pages: int) -> List[Dict]:
        """Scrape search results for a specific term"""
        listings = []
        
        search_url = f"{self.base_url}/search/?query={search_term.replace(' ', '%20')}"
        
        try:
            driver.get(search_url)
            time.sleep(5)  # Wait for page to load
            
            self._handle_popups(driver)
            
            for page in range(max_pages):
                try:
                    listing_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="marketplace-item"]')
                    
                    for element in listing_elements:
                        listing = self._parse_listing_element(element)
                        if listing and self.is_relevant_listing(listing['title'], listing.get('description', '')):
                            listings.append(listing)
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    new_listings = driver.find_elements(By.CSS_SELECTOR, '[data-testid="marketplace-item"]')
                    if len(new_listings) == len(listing_elements):
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error on page {page}: {e}")
                    break
            
        except Exception as e:
            self.logger.error(f"Error navigating to Facebook search: {e}")
        
        return listings
    
    def _handle_popups(self, driver):
        """Handle Facebook popups and overlays"""
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="cookie-policy-manage-dialog-accept-button"]'))
            )
            cookie_button.click()
        except TimeoutException:
            pass
        
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, '[aria-label="Close"]')
            close_button.click()
        except NoSuchElementException:
            pass
    
    def _parse_listing_element(self, element) -> Dict:
        """Parse individual Facebook Marketplace listing element"""
        try:
            title_elem = element.find_element(By.CSS_SELECTOR, 'span[dir="auto"]')
            title = title_elem.text.strip() if title_elem else ""
            
            price_elem = element.find_element(By.CSS_SELECTOR, 'span[dir="auto"]')
            price_text = price_elem.text.strip() if price_elem else ""
            price = self.extract_price(price_text)
            
            location_elem = element.find_element(By.CSS_SELECTOR, 'span[color="secondary"]')
            location = location_elem.text.strip() if location_elem else ""
            
            link_elem = element.find_element(By.TAG_NAME, 'a')
            url = link_elem.get_attribute('href') if link_elem else ""
            
            img_elem = element.find_element(By.TAG_NAME, 'img')
            image_url = img_elem.get_attribute('src') if img_elem else ""
            image_urls = [image_url] if image_url else []
            
            condition_keywords = self.extract_condition_keywords(title)
            
            listing = {
                'platform': self.get_platform_name(),
                'title': title,
                'url': url,
                'price': price,
                'location': location,
                'seller_name': "Facebook User",
                'description': "",
                'image_urls': image_urls,
                'condition_keywords': condition_keywords
            }
            
            return listing
            
        except Exception as e:
            self.logger.error(f"Error parsing Facebook listing: {e}")
            return None

    def _get_listing_details(self, driver, url: str) -> Dict:
        """Get detailed information from Facebook listing page"""
        try:
            driver.get(url)
            time.sleep(3)
            
            description = ""
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, '[data-testid="post_message"]')
                description = desc_elem.text.strip()
            except NoSuchElementException:
                pass
            
            seller_name = "Facebook User"
            try:
                seller_elem = driver.find_element(By.CSS_SELECTOR, '[data-testid="seller_name"]')
                seller_name = seller_elem.text.strip()
            except NoSuchElementException:
                pass
            
            return {
                'description': description,
                'seller_name': seller_name
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Facebook listing details: {e}")
            return {'description': '', 'seller_name': 'Facebook User'}
