import requests
import json
import logging
from typing import Dict, List

class DiscordNotifier:
    def __init__(self, config):
        self.config = config
        self.webhook_url = config.DISCORD_WEBHOOK_URL
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def send_hot_deal_alert(self, listing: Dict) -> bool:
        """Send a hot deal alert to Discord"""
        if not self.webhook_url:
            self.logger.warning("Discord webhook URL not configured")
            return False
        
        try:
            embed = self._create_deal_embed(listing)
            payload = {
                "content": "🔥 **HOT ENGINE DEAL ALERT!** 🔥",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 204:
                self.logger.info(f"Discord alert sent for listing: {listing.get('title', 'Unknown')}")
                return True
            else:
                self.logger.error(f"Discord webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Discord notification: {e}")
            return False
    
    def send_daily_summary(self, hot_deals: List[Dict], total_new_listings: int) -> bool:
        """Send daily summary of deals"""
        if not self.webhook_url:
            return False
        
        try:
            embed = {
                "title": "📊 Daily Engine Deals Summary",
                "color": 0x00ff00,
                "fields": [
                    {
                        "name": "New Listings Today",
                        "value": str(total_new_listings),
                        "inline": True
                    },
                    {
                        "name": "Hot Deals Found",
                        "value": str(len(hot_deals)),
                        "inline": True
                    }
                ],
                "timestamp": self._get_timestamp()
            }
            
            if hot_deals:
                top_deals_text = ""
                for i, deal in enumerate(hot_deals[:5], 1):
                    price = f"${deal.get('price', 'N/A')}" if deal.get('price') else "Price N/A"
                    score = f"{deal.get('deal_score', 0):.2f}"
                    top_deals_text += f"{i}. **{deal.get('title', 'Unknown')[:50]}...** - {price} (Score: {score})\n"
                
                embed["fields"].append({
                    "name": "🏆 Top Hot Deals",
                    "value": top_deals_text[:1024],  # Discord field limit
                    "inline": False
                })
            
            payload = {
                "content": "📈 Your daily engine deals report is ready!",
                "embeds": [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 204
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            return False
    
    def _create_deal_embed(self, listing: Dict) -> Dict:
        """Create Discord embed for a deal listing"""
        title = listing.get('title', 'Unknown Listing')[:256]  # Discord title limit
        price = listing.get('price')
        price_text = f"${price:,.2f}" if price else "Price not listed"
        
        embed = {
            "title": title,
            "url": listing.get('url', ''),
            "color": 0xff6b35,  # Orange color for hot deals
            "fields": [
                {
                    "name": "💰 Price",
                    "value": price_text,
                    "inline": True
                },
                {
                    "name": "🏪 Platform",
                    "value": listing.get('platform', 'Unknown').title(),
                    "inline": True
                },
                {
                    "name": "📍 Location",
                    "value": listing.get('location', 'Not specified')[:100],
                    "inline": True
                },
                {
                    "name": "⭐ Deal Score",
                    "value": f"{listing.get('deal_score', 0):.2f}/1.00",
                    "inline": True
                },
                {
                    "name": "👤 Seller",
                    "value": listing.get('seller_name', 'Unknown')[:100],
                    "inline": True
                }
            ],
            "timestamp": self._get_timestamp()
        }
        
        description = listing.get('description', '')
        if description:
            embed["description"] = description[:500] + "..." if len(description) > 500 else description
        
        image_urls = listing.get('image_urls', [])
        if image_urls and isinstance(image_urls, list) and len(image_urls) > 0:
            embed["image"] = {"url": image_urls[0]}
        elif isinstance(image_urls, str):
            try:
                urls = json.loads(image_urls)
                if urls and len(urls) > 0:
                    embed["image"] = {"url": urls[0]}
            except:
                pass
        
        condition_keywords = listing.get('condition_keywords', [])
        if condition_keywords:
            if isinstance(condition_keywords, str):
                try:
                    condition_keywords = json.loads(condition_keywords)
                except:
                    condition_keywords = []
            
            if condition_keywords:
                keywords_text = ", ".join(condition_keywords[:10])  # Limit keywords
                embed["fields"].append({
                    "name": "🔧 Condition Keywords",
                    "value": keywords_text[:1024],
                    "inline": False
                })
        
        return embed
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def test_webhook(self) -> bool:
        """Test Discord webhook connection"""
        if not self.webhook_url:
            self.logger.error("No Discord webhook URL configured")
            return False
        
        try:
            test_payload = {
                "content": "🤖 Engine Deals AI - Test notification successful!"
            }
            
            response = requests.post(self.webhook_url, json=test_payload, timeout=10)
            
            if response.status_code == 204:
                self.logger.info("Discord webhook test successful")
                return True
            else:
                self.logger.error(f"Discord webhook test failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Discord webhook test error: {e}")
            return False
