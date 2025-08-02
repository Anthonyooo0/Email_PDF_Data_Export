# Engine Deals AI

An AI-powered system that scrapes engine parts listings from multiple platforms and identifies the best deals using machine learning.

## Features

- **Multi-platform scraping**: Facebook Marketplace, eBay, OfferUp, Craigslist
- **Smart deal detection**: ML model trained to identify good deals based on price, condition, location
- **Automated notifications**: Email/Discord alerts for hot deals
- **Focus on Chevy V8 LQ4**: Specialized for specific engine types

## Architecture

```
scrapers/          # Platform-specific scrapers
├── facebook.py
├── ebay.py
├── offerup.py
└── craigslist.py

data/              # Data storage and processing
├── database.py
├── models.py
└── preprocessing.py

ml/                # Machine learning components
├── feature_engineering.py
├── model_training.py
└── scoring.py

notifications/     # Alert system
├── discord_bot.py
└── email_sender.py

scheduler/         # Automation
└── job_scheduler.py
```

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure settings in `config.py`
3. Run initial scraping: `python main.py --scrape`
4. Train model: `python main.py --train`
5. Start monitoring: `python main.py --monitor`
