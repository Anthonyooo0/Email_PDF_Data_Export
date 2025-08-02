import sqlite3
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                price REAL,
                location TEXT,
                seller_name TEXT,
                url TEXT UNIQUE,
                image_urls TEXT,  -- JSON array of image URLs
                condition_keywords TEXT,  -- JSON array of extracted keywords
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                deal_score REAL,
                is_hot_deal BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER,
                is_good_deal BOOLEAN,
                user_rating INTEGER,  -- 1-5 scale
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER,
                notification_type TEXT,  -- 'email', 'discord'
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN,
                FOREIGN KEY (listing_id) REFERENCES listings (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_listing(self, listing_data: Dict) -> int:
        """Insert a new listing and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO listings 
                (platform, title, description, price, location, seller_name, url, 
                 image_urls, condition_keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                listing_data['platform'],
                listing_data['title'],
                listing_data.get('description', ''),
                listing_data.get('price'),
                listing_data.get('location', ''),
                listing_data.get('seller_name', ''),
                listing_data['url'],
                json.dumps(listing_data.get('image_urls', [])),
                json.dumps(listing_data.get('condition_keywords', []))
            ))
            
            listing_id = cursor.lastrowid
            conn.commit()
            return listing_id
            
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def update_deal_score(self, listing_id: int, score: float, is_hot_deal: bool = False):
        """Update the deal score for a listing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE listings 
            SET deal_score = ?, is_hot_deal = ?
            WHERE id = ?
        ''', (score, is_hot_deal, listing_id))
        
        conn.commit()
        conn.close()
    
    def get_listings_for_training(self) -> pd.DataFrame:
        """Get listings data for ML training"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT l.*, t.is_good_deal, t.user_rating
            FROM listings l
            LEFT JOIN training_data t ON l.id = t.listing_id
            WHERE l.price IS NOT NULL AND l.price > 0
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_recent_listings(self, hours: int = 24) -> pd.DataFrame:
        """Get listings from the last N hours"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM listings 
            WHERE scraped_at >= datetime('now', '-{} hours')
            AND is_active = TRUE
            ORDER BY scraped_at DESC
        '''.format(hours)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_hot_deals(self, limit: int = 20) -> pd.DataFrame:
        """Get current hot deals"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM listings 
            WHERE is_hot_deal = TRUE 
            AND is_active = TRUE
            ORDER BY deal_score DESC, scraped_at DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        return df
    
    def add_training_label(self, listing_id: int, is_good_deal: bool, 
                          user_rating: int = None, notes: str = None):
        """Add training label for a listing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO training_data 
            (listing_id, is_good_deal, user_rating, notes)
            VALUES (?, ?, ?, ?)
        ''', (listing_id, is_good_deal, user_rating, notes))
        
        conn.commit()
        conn.close()
    
    def log_notification(self, listing_id: int, notification_type: str, success: bool):
        """Log a notification attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (listing_id, notification_type, success)
            VALUES (?, ?, ?)
        ''', (listing_id, notification_type, success))
        
        conn.commit()
        conn.close()
