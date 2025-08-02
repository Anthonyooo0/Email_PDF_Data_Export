#!/usr/bin/env python3
"""
Engine Deals AI - Main Application
Scrapes engine parts from multiple platforms and identifies hot deals using ML
"""

import argparse
import logging
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from data.database import DatabaseManager
from scraper_manager import ScraperManager
from ml.model_training import DealScoreModel
from notifications.discord_bot import DiscordNotifier
from notifications.email_sender import EmailNotifier
from scheduler.job_scheduler import JobScheduler

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('engine_deals.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_directories():
    """Create necessary directories"""
    os.makedirs('data', exist_ok=True)
    os.makedirs('ml', exist_ok=True)
    os.makedirs('logs', exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description='Engine Deals AI')
    parser.add_argument('--scrape', action='store_true', help='Run scraping job')
    parser.add_argument('--train', action='store_true', help='Train ML model')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring mode')
    parser.add_argument('--test', action='store_true', help='Test all components')
    parser.add_argument('--platform', type=str, help='Test specific platform')
    parser.add_argument('--summary', action='store_true', help='Generate daily summary')
    
    args = parser.parse_args()
    
    setup_logging()
    setup_directories()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Engine Deals AI...")
    
    config = Config()
    database = DatabaseManager(config.DATABASE_PATH)
    scraper_manager = ScraperManager(config)
    model = DealScoreModel(config)
    
    notifiers = {}
    if config.DISCORD_WEBHOOK_URL:
        notifiers['discord'] = DiscordNotifier(config)
    if config.EMAIL_USERNAME and config.EMAIL_PASSWORD:
        notifiers['email'] = EmailNotifier(config)
    
    try:
        if args.test:
            run_tests(scraper_manager, model, database, notifiers, logger)
        elif args.scrape:
            run_scraping(scraper_manager, database, model, notifiers, logger)
        elif args.train:
            run_training(model, database, logger)
        elif args.monitor:
            run_monitoring(scraper_manager, model, database, notifiers, logger)
        elif args.platform:
            test_platform(scraper_manager, args.platform, logger)
        elif args.summary:
            generate_summary(database, notifiers, logger)
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def run_tests(scraper_manager, model, database, notifiers, logger):
    """Run comprehensive tests"""
    logger.info("Running comprehensive tests...")
    
    logger.info("Testing scrapers...")
    scraper_results = scraper_manager.test_scrapers()
    for platform, success in scraper_results.items():
        logger.info(f"  {platform}: {'✓' if success else '✗'}")
    
    logger.info("Testing database...")
    import time
    test_listing = {
        'platform': 'test',
        'title': 'Test LQ4 Engine',
        'url': f'http://test.com/test-listing-{int(time.time())}',
        'price': 1500.0,
        'location': 'Test City',
        'seller_name': 'Test Seller',
        'description': 'Test description',
        'image_urls': [],
        'condition_keywords': ['good_rebuilt']
    }
    
    try:
        listing_id = database.insert_listing(test_listing)
        if listing_id:
            logger.info("  Database: ✓")
            database.update_deal_score(listing_id, 0.85, True)
        else:
            logger.error("  Database: ✗ - Failed to insert listing")
    except Exception as e:
        logger.error(f"  Database: ✗ - Exception: {e}")
    
    logger.info("Testing ML model...")
    try:
        import pandas as pd
        synthetic_df = pd.DataFrame([test_listing])
        metrics = model.train_model(synthetic_df)
        logger.info(f"  Model training: ✓ (R² = {metrics.get('r2', 0):.3f})")
    except Exception as e:
        logger.error(f"  Model training: ✗ ({e})")
    
    logger.info("Testing notifications...")
    for name, notifier in notifiers.items():
        try:
            if hasattr(notifier, 'test_webhook'):
                success = notifier.test_webhook()
            elif hasattr(notifier, 'test_email'):
                success = notifier.test_email()
            else:
                success = False
            logger.info(f"  {name}: {'✓' if success else '✗'}")
        except Exception as e:
            logger.error(f"  {name}: ✗ ({e})")

def run_scraping(scraper_manager, database, model, notifiers, logger):
    """Run scraping job"""
    logger.info("Starting scraping job...")
    
    all_listings = scraper_manager.scrape_all_platforms()
    
    if not all_listings:
        logger.warning("No listings found")
        return
    
    new_listings = []
    for listing in all_listings:
        listing_id = database.insert_listing(listing)
        if listing_id:
            listing['id'] = listing_id
            new_listings.append(listing)
    
    logger.info(f"Added {len(new_listings)} new listings")
    
    if new_listings:
        try:
            if model.load_model():
                score_listings(new_listings, model, database, notifiers, logger)
            else:
                logger.info("No trained model available. Run --train first.")
        except Exception as e:
            logger.error(f"Error scoring listings: {e}")

def score_listings(listings, model, database, notifiers, logger):
    """Score listings and send notifications"""
    import pandas as pd
    
    df = pd.DataFrame(listings)
    scores = model.predict_deal_scores(df)
    
    hot_deals = []
    for listing, score in zip(listings, scores):
        is_hot_deal = score >= model.config.HOT_DEAL_THRESHOLD
        
        database.update_deal_score(listing['id'], float(score), is_hot_deal)
        
        if is_hot_deal:
            listing['deal_score'] = float(score)
            hot_deals.append(listing)
    
    logger.info(f"Found {len(hot_deals)} hot deals")
    
    for deal in hot_deals:
        for name, notifier in notifiers.items():
            try:
                if name == 'discord':
                    success = notifier.send_hot_deal_alert(deal)
                elif name == 'email':
                    success = notifier.send_hot_deal_alert(deal)
                else:
                    success = False
                
                database.log_notification(deal['id'], name, success)
            except Exception as e:
                logger.error(f"Error sending {name} notification: {e}")

def run_training(model, database, logger):
    """Train ML model"""
    logger.info("Starting model training...")
    
    training_df = database.get_listings_for_training()
    
    if len(training_df) < 10:
        logger.info("Not enough real data, using synthetic data for initial training")
    
    metrics = model.train_model(training_df)
    model.save_model()
    
    logger.info(f"Model trained successfully!")
    logger.info(f"  R² score: {metrics.get('r2', 0):.3f}")
    logger.info(f"  Training samples: {metrics.get('training_samples', 0)}")
    logger.info(f"  Test samples: {metrics.get('test_samples', 0)}")

def run_monitoring(scraper_manager, model, database, notifiers, logger):
    """Start monitoring mode"""
    logger.info("Starting monitoring mode...")
    
    if not model.load_model():
        logger.error("No trained model found. Run --train first.")
        return
    
    scheduler = JobScheduler(scraper_manager, model, database, notifiers)
    scheduler.start_scheduler()
    
    logger.info("Monitoring started. Press Ctrl+C to stop.")
    
    try:
        while True:
            import time
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopping monitoring...")
        scheduler.stop_scheduler()

def test_platform(scraper_manager, platform_name, logger):
    """Test specific platform"""
    logger.info(f"Testing {platform_name} scraper...")
    
    try:
        listings = scraper_manager.scrape_platform(platform_name)
        logger.info(f"Found {len(listings)} listings")
        
        for i, listing in enumerate(listings[:3]):
            logger.info(f"  {i+1}. {listing.get('title', 'No title')[:50]}... - ${listing.get('price', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error testing {platform_name}: {e}")

def generate_summary(database, notifiers, logger):
    """Generate daily summary"""
    logger.info("Generating daily summary...")
    
    recent_df = database.get_recent_listings(hours=24)
    hot_deals_df = database.get_hot_deals(limit=20)
    
    total_new_listings = len(recent_df)
    hot_deals = hot_deals_df.to_dict('records') if not hot_deals_df.empty else []
    
    logger.info(f"Summary: {total_new_listings} new listings, {len(hot_deals)} hot deals")
    
    for name, notifier in notifiers.items():
        try:
            if name == 'discord':
                notifier.send_daily_summary(hot_deals, total_new_listings)
            elif name == 'email':
                notifier.send_daily_summary(hot_deals, total_new_listings)
        except Exception as e:
            logger.error(f"Error sending {name} summary: {e}")

if __name__ == "__main__":
    main()
