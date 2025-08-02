import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_PATH = "data/engine_deals.db"
    
    SCRAPE_INTERVAL_HOURS = 6
    MAX_PAGES_PER_SITE = 5
    REQUEST_DELAY = (2, 5)  # Random delay between requests
    
    SEARCH_TERMS = [
        "LQ4 engine",
        "Chevy V8 engine",
        "LS engine",
        "Vortec engine",
        "5.3 engine",
        "6.0 engine",
        "engine block",
        "cylinder heads",
        "intake manifold",
        "crankshaft",
        "pistons",
        "connecting rods"
    ]
    
    GOOD_CONDITION_KEYWORDS = [
        "rebuilt", "remanufactured", "new", "excellent", "perfect",
        "low miles", "fresh rebuild", "zero miles", "unused"
    ]
    
    BAD_CONDITION_KEYWORDS = [
        "spun bearing", "cracked", "damaged", "blown", "seized",
        "needs work", "for parts", "rebuild needed", "bad"
    ]
    
    MODEL_PATH = "ml/trained_model.pkl"
    FEATURE_SCALER_PATH = "ml/feature_scaler.pkl"
    
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")
    
    HOT_DEAL_THRESHOLD = 0.8  # Score above this triggers notification
    GOOD_DEAL_THRESHOLD = 0.6
    
    USER_LOCATION = {
        "lat": 40.7128,  # Default to NYC, user can update
        "lon": -74.0060
    }
    MAX_DISTANCE_MILES = 500
