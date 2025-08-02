import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import List
import threading

class JobScheduler:
    def __init__(self, scraper_manager, model, database, notifiers):
        self.scraper_manager = scraper_manager
        self.model = model
        self.database = database
        self.notifiers = notifiers
        self.logger = logging.getLogger(self.__class__.__name__)
        self.running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """Start the job scheduler"""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.logger.info("Starting job scheduler...")
        
        schedule.every(6).hours.do(self._run_scraping_job)
        schedule.every().day.at("08:00").do(self._run_daily_summary)
        schedule.every().day.at("20:00").do(self._run_model_retraining)
        
        self._run_scraping_job()
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Job scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the job scheduler"""
        self.logger.info("Stopping job scheduler...")
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        schedule.clear()
        self.logger.info("Job scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)
    
    def _run_scraping_job(self):
        """Run the scraping job"""
        self.logger.info("Starting scheduled scraping job...")
        
        try:
            all_listings = self.scraper_manager.scrape_all_platforms()
            
            if not all_listings:
                self.logger.warning("No listings found during scraping")
                return
            
            self.logger.info(f"Scraped {len(all_listings)} listings")
            
            new_listings = []
            for listing in all_listings:
                listing_id = self.database.insert_listing(listing)
                if listing_id:  # New listing
                    listing['id'] = listing_id
                    new_listings.append(listing)
            
            self.logger.info(f"Added {len(new_listings)} new listings to database")
            
            if new_listings:
                self._score_and_notify_listings(new_listings)
            
        except Exception as e:
            self.logger.error(f"Error in scraping job: {e}")
    
    def _score_and_notify_listings(self, listings: List[dict]):
        """Score listings and send notifications for hot deals"""
        try:
            if not self.model.model:
                if not self.model.load_model():
                    self.logger.warning("No trained model available, using heuristic scoring")
                    return
            
            import pandas as pd
            df = pd.DataFrame(listings)
            
            scores = self.model.predict_deal_scores(df)
            
            hot_deals = []
            for i, (listing, score) in enumerate(zip(listings, scores)):
                is_hot_deal = score >= self.model.config.HOT_DEAL_THRESHOLD
                
                self.database.update_deal_score(
                    listing['id'], 
                    float(score), 
                    is_hot_deal
                )
                
                if is_hot_deal:
                    listing['deal_score'] = float(score)
                    listing['is_hot_deal'] = True
                    hot_deals.append(listing)
            
            self.logger.info(f"Found {len(hot_deals)} hot deals")
            
            for deal in hot_deals:
                self._send_hot_deal_notifications(deal)
            
        except Exception as e:
            self.logger.error(f"Error scoring listings: {e}")
    
    def _send_hot_deal_notifications(self, deal: dict):
        """Send notifications for a hot deal"""
        try:
            if 'discord' in self.notifiers:
                success = self.notifiers['discord'].send_hot_deal_alert(deal)
                self.database.log_notification(deal['id'], 'discord', success)
            
            if 'email' in self.notifiers:
                success = self.notifiers['email'].send_hot_deal_alert(deal)
                self.database.log_notification(deal['id'], 'email', success)
            
            self.logger.info(f"Sent notifications for hot deal: {deal.get('title', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error sending notifications for deal {deal.get('id')}: {e}")
    
    def _run_daily_summary(self):
        """Send daily summary of deals"""
        self.logger.info("Generating daily summary...")
        
        try:
            recent_df = self.database.get_recent_listings(hours=24)
            hot_deals_df = self.database.get_hot_deals(limit=20)
            
            total_new_listings = len(recent_df)
            hot_deals = hot_deals_df.to_dict('records') if not hot_deals_df.empty else []
            
            self.logger.info(f"Daily summary: {total_new_listings} new listings, {len(hot_deals)} hot deals")
            
            if 'discord' in self.notifiers:
                self.notifiers['discord'].send_daily_summary(hot_deals, total_new_listings)
            
            if 'email' in self.notifiers:
                self.notifiers['email'].send_daily_summary(hot_deals, total_new_listings)
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {e}")
    
    def _run_model_retraining(self):
        """Retrain the model with new data"""
        self.logger.info("Starting model retraining...")
        
        try:
            training_df = self.database.get_listings_for_training()
            
            if len(training_df) < 50:
                self.logger.info("Not enough data for retraining, skipping...")
                return
            
            metrics = self.model.train_model(training_df)
            self.model.save_model()
            
            self.logger.info(f"Model retrained successfully. R² score: {metrics.get('r2', 0):.3f}")
            
        except Exception as e:
            self.logger.error(f"Error retraining model: {e}")
    
    def run_manual_scraping(self):
        """Run scraping manually (for testing)"""
        self.logger.info("Running manual scraping...")
        self._run_scraping_job()
    
    def run_manual_summary(self):
        """Run daily summary manually (for testing)"""
        self.logger.info("Running manual daily summary...")
        self._run_daily_summary()
