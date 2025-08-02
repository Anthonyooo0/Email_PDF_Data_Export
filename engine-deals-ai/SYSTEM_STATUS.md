# Engine Deals AI - System Status Report

## 🎯 Project Overview
Complete AI system that scrapes engine part listings from multiple online marketplaces, trains a machine learning model to score deals, and notifies users of "hot deals."

## ✅ Working Components

### 1. Craigslist Scraper
- **Status**: ✅ WORKING (107 listings found in tests)
- **Coverage**: Multiple major cities (Los Angeles, Chicago, Houston, Phoenix, etc.)
- **Features**: Extracts title, price, location, seller, description, images
- **Rate Limiting**: Some 403 errors on certain cities, but overall functional

### 2. Database System
- **Status**: ✅ WORKING
- **Type**: SQLite database
- **Features**: 
  - Stores listings with duplicate prevention (unique URL constraint)
  - Tracks deal scores and hot deal flags
  - Maintains training data and notification logs
  - Supports ML model training data retrieval

### 3. Machine Learning Model
- **Status**: ✅ WORKING (R² score: 0.251)
- **Type**: Random Forest Regressor with feature engineering
- **Key Features**:
  - LQ4 priority scoring (highest weight: 0.194)
  - Condition keyword analysis (weight: 0.189)
  - Price analysis and distance estimation
  - Rebuilt/remanufactured detection
- **Training**: Uses synthetic data initially, can learn from real data over time

### 4. Notification System
- **Status**: ✅ IMPLEMENTED
- **Options**: Discord webhook and Email notifications
- **Features**: Hot deal alerts and daily summaries

### 5. Job Scheduler
- **Status**: ✅ IMPLEMENTED
- **Features**: Automated daily scraping and monitoring

## ⚠️ Partially Working / Blocked Components

### 1. eBay Scraper
- **Status**: ⚠️ RATE LIMITED
- **Issue**: eBay is returning 503 Service Unavailable errors due to aggressive scraping detection
- **Previous Success**: Successfully scraped 3,198 listings before being blocked
- **Solution**: Implement longer delays, proxy rotation, or different scraping approach

### 2. Facebook Marketplace Scraper
- **Status**: ⚠️ BLOCKED
- **Issue**: Facebook's anti-bot measures prevent headless browser access
- **Challenge**: Requires login and sophisticated bot detection evasion
- **Solution**: May need residential proxies or different approach

### 3. OfferUp Scraper
- **Status**: ⚠️ BLOCKED
- **Issue**: 403 Forbidden errors on all requests
- **Challenge**: Strong anti-scraping protection
- **Solution**: Requires different scraping strategy or proxy usage

## 🚀 System Capabilities

### Current Functionality
1. **Automated Scraping**: Craigslist across multiple cities
2. **Data Storage**: SQLite database with proper schema
3. **ML Scoring**: Trained model identifies good deals based on:
   - LQ4 engine priority
   - Condition keywords (rebuilt, excellent, etc.)
   - Price analysis
   - Location distance estimation
4. **Notifications**: Discord/Email alerts for hot deals
5. **Monitoring**: Scheduled daily runs

### Search Terms Supported
- LQ4 engine (primary focus)
- Chevy V8 engine
- LS engine
- Vortec engine
- 5.3 engine, 6.0 engine
- Engine block, cylinder heads
- Intake manifold, crankshaft
- Pistons, connecting rods

## 📊 Performance Metrics

### Recent Test Results
- **Craigslist**: 107 listings scraped successfully
- **Database**: 100% insertion success rate
- **ML Model**: R² = 0.251 (reasonable for initial model)
- **Feature Importance**: LQ4 priority (19.4%), Condition (18.9%)

### Hot Deal Threshold
- **Current Setting**: 0.8 (80% confidence score)
- **Good Deal Threshold**: 0.6 (60% confidence score)

## 🛠️ Technical Architecture

### Core Technologies
- **Python 3.12** with pyenv
- **Selenium + ChromeDriver** for web scraping
- **SQLite** for data storage
- **Scikit-learn** for machine learning
- **Requests + BeautifulSoup** for HTTP scraping
- **APScheduler** for job scheduling

### Project Structure
```
engine-deals-ai/
├── scrapers/          # Web scraping modules
├── data/             # Database and storage
├── ml/               # Machine learning components
├── notifications/    # Alert systems
├── scheduler/        # Job scheduling
├── config.py         # Configuration
├── main.py          # Main application
└── requirements.txt  # Dependencies
```

## 🎯 Recommendations

### Immediate Actions
1. **Deploy Current System**: The Craigslist scraper alone provides valuable functionality
2. **Monitor Performance**: Track ML model accuracy as real data accumulates
3. **Gradual Expansion**: Add other platforms when anti-bot measures can be bypassed

### Future Improvements
1. **Proxy Integration**: Implement rotating proxies for blocked platforms
2. **Enhanced ML**: Retrain model with more real data for better accuracy
3. **Additional Features**: Price trend analysis, seller reputation scoring
4. **Mobile App**: Create mobile interface for deal notifications

## 🔧 Setup Instructions
See README.md for complete installation and configuration instructions.

---
*Last Updated: August 1, 2025*
*System Version: 1.0*
