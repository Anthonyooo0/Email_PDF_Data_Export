#!/usr/bin/env python3
"""
Debug script to test database functionality
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from data.database import DatabaseManager

def test_database():
    print("Testing database functionality...")
    
    config = Config()
    database = DatabaseManager(config.DATABASE_PATH)
    
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
    
    print(f"Test listing data: {test_listing}")
    
    try:
        print("Attempting to insert listing...")
        listing_id = database.insert_listing(test_listing)
        print(f"Insert result: {listing_id}")
        
        if listing_id:
            print("✓ Database insertion successful")
            
            print("Testing deal score update...")
            database.update_deal_score(listing_id, 0.85, True)
            print("✓ Deal score update successful")
            
        else:
            print("✗ Database insertion failed - returned None/False")
            
    except Exception as e:
        print(f"✗ Database insertion failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()
