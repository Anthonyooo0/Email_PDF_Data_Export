# Engine Deals AI - Complete Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (recommended: 3.12)
- Chrome browser installed
- Git

### 1. Installation
```bash
# Clone or download the project
cd engine-deals-ai

# Install Python dependencies
pip install -r requirements.txt

# Install ChromeDriver (for Selenium)
# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install chromium-chromedriver

# On macOS:
brew install chromedriver

# On Windows:
# Download ChromeDriver from https://chromedriver.chromium.org/
# Add to PATH
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env
```

### 3. Basic Test
```bash
# Test the system
python main.py --test

# Test individual scraper
python main.py --platform craigslist
```

## ⚙️ Configuration Options

### Environment Variables (.env file)
```bash
# Discord Notifications (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url

# Email Notifications (optional)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
NOTIFICATION_EMAIL=recipient@gmail.com
```

### Config.py Settings
```python
# Scraping Settings
MAX_PAGES_PER_SITE = 5          # Pages to scrape per platform
REQUEST_DELAY = (2, 5)          # Random delay between requests
SCRAPE_INTERVAL_HOURS = 6       # How often to run scraping

# ML Model Settings
HOT_DEAL_THRESHOLD = 0.8        # Score threshold for hot deals
GOOD_DEAL_THRESHOLD = 0.6       # Score threshold for good deals

# Location Settings (update with your location)
USER_LOCATION = {
    "lat": 40.7128,             # Your latitude
    "lon": -74.0060             # Your longitude
}
MAX_DISTANCE_MILES = 500        # Maximum distance for deals
```

## 🎯 Usage Examples

### 1. Run Complete System Test
```bash
python main.py --test
```
This tests all components: scrapers, database, ML model, and notifications.

### 2. Scrape All Platforms
```bash
python main.py --scrape
```
Runs all scrapers and processes new listings through the ML model.

### 3. Train ML Model
```bash
python main.py --train
```
Trains the machine learning model on available data.

### 4. Start Monitoring Mode
```bash
python main.py --monitor
```
Starts automated monitoring with scheduled scraping.

### 5. Test Specific Platform
```bash
python main.py --platform craigslist
python main.py --platform ebay
python main.py --platform facebook
python main.py --platform offerup
```

### 6. Generate Daily Summary
```bash
python main.py --summary
```

## 🔧 Advanced Configuration

### Custom Search Terms
Edit `config.py` to modify search terms:
```python
SEARCH_TERMS = [
    "LQ4 engine",           # Primary focus
    "Chevy V8 engine",
    "LS engine",
    "Vortec engine",
    "5.3 engine",
    "6.0 engine",
    # Add your custom terms here
]
```

### Condition Keywords
Customize condition detection:
```python
GOOD_CONDITION_KEYWORDS = [
    "rebuilt", "remanufactured", "new", "excellent",
    "low miles", "fresh rebuild", "zero miles"
]

BAD_CONDITION_KEYWORDS = [
    "spun bearing", "cracked", "damaged", "blown",
    "needs work", "for parts", "rebuild needed"
]
```

### Database Location
```python
DATABASE_PATH = "data/engine_deals.db"  # Change if needed
```

## 📊 Monitoring and Maintenance

### View Database Contents
```python
import sqlite3
conn = sqlite3.connect('data/engine_deals.db')
cursor = conn.cursor()

# View recent listings
cursor.execute("SELECT * FROM listings ORDER BY created_at DESC LIMIT 10")
print(cursor.fetchall())

# View hot deals
cursor.execute("SELECT * FROM listings WHERE is_hot_deal = 1")
print(cursor.fetchall())
```

### Check Logs
```bash
# View application logs
tail -f engine_deals.log

# View recent activity
grep "hot deal" engine_deals.log
```

### Model Performance
The ML model will improve over time as it learns from real data. Initial R² score is around 0.25, which should improve with more training data.

## 🚨 Troubleshooting

### Common Issues

#### 1. ChromeDriver Not Found
```bash
# Install ChromeDriver
sudo apt-get install chromium-chromedriver

# Or download manually and add to PATH
```

#### 2. Scraper Getting Blocked (403/503 errors)
- Increase delays in `config.py`
- Use VPN or proxy
- Reduce scraping frequency

#### 3. No Notifications Received
- Check Discord webhook URL
- Verify email credentials
- Test with: `python -c "from notifications.discord_bot import DiscordNotifier; DiscordNotifier(config).test_webhook()"`

#### 4. Database Errors
```bash
# Reset database
rm data/engine_deals.db
python main.py --test  # Recreates database
```

#### 5. ML Model Not Training
- Ensure sufficient data (>10 listings)
- Check for data quality issues
- Review feature engineering in `ml/feature_engineering.py`

### Performance Optimization

#### 1. Faster Scraping
- Reduce `max_pages` in scraper calls
- Increase `REQUEST_DELAY` to avoid blocks
- Focus on most productive platforms

#### 2. Better ML Accuracy
- Add manual labels to training data
- Adjust feature weights in `ml/model_training.py`
- Collect more diverse training examples

#### 3. Notification Tuning
- Adjust `HOT_DEAL_THRESHOLD` based on results
- Customize notification templates
- Add filtering for specific engine types

## 🔄 Automation Setup

### Cron Job (Linux/macOS)
```bash
# Edit crontab
crontab -e

# Add line for every 6 hours
0 */6 * * * cd /path/to/engine-deals-ai && python main.py --scrape

# Daily summary at 8 AM
0 8 * * * cd /path/to/engine-deals-ai && python main.py --summary
```

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 8 AM)
4. Set action: Start Program
5. Program: `python`
6. Arguments: `main.py --scrape`
7. Start in: `C:\path\to\engine-deals-ai`

### Systemd Service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/engine-deals.service

# Add content:
[Unit]
Description=Engine Deals AI
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/engine-deals-ai
ExecStart=/usr/bin/python main.py --monitor
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable engine-deals.service
sudo systemctl start engine-deals.service
```

## 📈 Success Metrics

### What to Expect
- **Craigslist**: 50-200 listings per run
- **Hot Deals**: 1-5 per day (depends on threshold)
- **ML Accuracy**: Improves over time with more data
- **Response Time**: 2-10 minutes per full scraping cycle

### Key Performance Indicators
1. **Listing Volume**: Track daily listing counts
2. **Deal Quality**: Monitor hot deal accuracy
3. **Model Performance**: Watch R² score improvements
4. **User Satisfaction**: Track notification relevance

---

## 🆘 Support

For issues or questions:
1. Check logs in `engine_deals.log`
2. Review this guide and `SYSTEM_STATUS.md`
3. Test individual components with `--test` flag
4. Verify configuration in `.env` and `config.py`

The system is designed to be robust and self-recovering. Most issues resolve with proper configuration and patience for anti-bot measures to reset.
