#!/usr/bin/env python3
"""
Example script showing how to use the Engine Deals AI system
"""

import logging
import time
from pathlib import Path
import sys

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from data.database import DatabaseManager
from scraper_manager import ScraperManager
from ml.model_training import DealScoreModel
from notifications.discord_bot import DiscordNotifier

def setup_logging():
    """Setup logging for the example"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def example_basic_usage():
    """Example 1: Basic scraping and scoring"""
    print("=== EXAMPLE 1: Basic Usage ===")
    
    config = Config()
    database = DatabaseManager(config.DATABASE_PATH)
    scraper_manager = ScraperManager(config)
    model = DealScoreModel(config)
    
    print("Testing scrapers...")
    results = scraper_manager.test_scrapers()
    for platform, success in results.items():
        print(f"  {platform}: {'✓' if success else '✗'}")
    
    print("\nScraping Craigslist...")
    listings = scraper_manager.scrape_platform('craigslist')
    print(f"Found {len(listings)} listings")
    
    new_listings = []
    for listing in listings[:5]:  # Limit to first 5 for example
        listing_id = database.insert_listing(listing)
        if listing_id:
            listing['id'] = listing_id
            new_listings.append(listing)
    
    print(f"Stored {len(new_listings)} new listings")
    
    if new_listings:
        print("\nTraining ML model...")
        training_df = database.get_listings_for_training()
        metrics = model.train_model(training_df)
        print(f"Model R² score: {metrics.get('r2', 0):.3f}")
        
        import pandas as pd
        df = pd.DataFrame(new_listings)
        scores = model.predict_deal_scores(df)
        
        print("\nTop scored listings:")
        for listing, score in zip(new_listings, scores):
            print(f"  Score: {score:.3f} - {listing['title'][:50]}... - ${listing['price']}")

def example_hot_deal_detection():
    """Example 2: Hot deal detection and notifications"""
    print("\n=== EXAMPLE 2: Hot Deal Detection ===")
    
    config = Config()
    database = DatabaseManager(config.DATABASE_PATH)
    model = DealScoreModel(config)
    
    if not model.load_model():
        print("No trained model found. Run example_basic_usage() first.")
        return
    
    recent_df = database.get_recent_listings(hours=24)
    if recent_df.empty:
        print("No recent listings found.")
        return
    
    scores = model.predict_deal_scores(recent_df)
    
    hot_deals = []
    for idx, (_, listing) in enumerate(recent_df.iterrows()):
        score = scores[idx]
        if score >= config.HOT_DEAL_THRESHOLD:
            listing_dict = listing.to_dict()
            listing_dict['deal_score'] = float(score)
            hot_deals.append(listing_dict)
            
            database.update_deal_score(listing['id'], float(score), True)
    
    print(f"Found {len(hot_deals)} hot deals!")
    
    for deal in hot_deals:
        print(f"🔥 HOT DEAL (Score: {deal['deal_score']:.3f})")
        print(f"   {deal['title']}")
        print(f"   ${deal['price']} - {deal['location']}")
        print(f"   {deal['url']}")
        print()
    
    if config.DISCORD_WEBHOOK_URL and hot_deals:
        print("Sending Discord notifications...")
        notifier = DiscordNotifier(config)
        for deal in hot_deals[:3]:  # Limit to 3 notifications
            success = notifier.send_hot_deal_alert(deal)
            print(f"  Discord notification: {'✓' if success else '✗'}")

def example_monitoring_setup():
    """Example 3: Setting up automated monitoring"""
    print("\n=== EXAMPLE 3: Monitoring Setup ===")
    
    from scheduler.job_scheduler import JobScheduler
    
    config = Config()
    database = DatabaseManager(config.DATABASE_PATH)
    scraper_manager = ScraperManager(config)
    model = DealScoreModel(config)
    
    notifiers = {}
    if config.DISCORD_WEBHOOK_URL:
        notifiers['discord'] = DiscordNotifier(config)
    
    scheduler = JobScheduler(scraper_manager, model, database, notifiers)
    
    print("Starting monitoring mode...")
    print("This will run automated scraping every 6 hours.")
    print("Press Ctrl+C to stop.")
    
    try:
        scheduler.start_scheduler()
        
        while True:
            time.sleep(60)
            print("Monitoring active... (Ctrl+C to stop)")
            
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        scheduler.stop_scheduler()
        print("Monitoring stopped.")

def example_data_analysis():
    """Example 4: Analyzing scraped data"""
    print("\n=== EXAMPLE 4: Data Analysis ===")
    
    config = Config()
    database = DatabaseManager(config.DATABASE_PATH)
    
    import sqlite3
    conn = sqlite3.connect(config.DATABASE_PATH)
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM listings")
    total_listings = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM listings WHERE is_hot_deal = 1")
    hot_deals = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(price) FROM listings WHERE price > 0")
    avg_price = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT platform, COUNT(*) FROM listings GROUP BY platform")
    platform_counts = cursor.fetchall()
    
    print(f"Total listings: {total_listings}")
    print(f"Hot deals: {hot_deals}")
    print(f"Average price: ${avg_price:.2f}")
    print("\nListings by platform:")
    for platform, count in platform_counts:
        print(f"  {platform}: {count}")
    
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count 
        FROM listings 
        WHERE created_at >= date('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """)
    recent_activity = cursor.fetchall()
    
    print("\nRecent activity (last 7 days):")
    for date, count in recent_activity:
        print(f"  {date}: {count} listings")
    
    conn.close()

def main():
    """Run all examples"""
    setup_logging()
    
    print("🚗 Engine Deals AI - Example Usage")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_hot_deal_detection()
        example_data_analysis()
        
        print("\n" + "=" * 50)
        print("✅ Examples completed successfully!")
        print("\nTo run monitoring mode:")
        print("  python run_example.py --monitor")
        print("\nTo run individual examples:")
        print("  python -c 'from run_example import example_basic_usage; example_basic_usage()'")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        setup_logging()
        example_monitoring_setup()
    else:
        main()
