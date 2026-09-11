# src/python/telegram_bot.py
import requests
import asyncio
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{token}"
        
        self.rate_limits = {}
        self.min_interval = 5  # seconds between same type alerts
    
    def send_alert(self, message: str, image_path: Optional[str] = None, 
                   alert_type: str = "default") -> bool:
        """Send alert to Telegram"""
        import time
        from pathlib import Path
        
        # Rate limiting
        current_time = time.time()
        last_time = self.rate_limits.get(alert_type, 0)
        if current_time - last_time < self.min_interval:
            logger.info(f"Skipping {alert_type} alert due to rate limit")
            return False
        
        try:
            if image_path and Path(image_path).exists():
                with open(image_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {
                        'chat_id': self.chat_id,
                        'caption': message,
                        'parse_mode': 'HTML'
                    }
                    response = requests.post(
                        f"{self.api_url}/sendPhoto",
                        files=files,
                        data=data,
                        timeout=10
                    )
            else:
                data = {
                    'chat_id': self.chat_id,
                    'text': f"🚨 <b>CCTV Alert</b>\n\n{message}",
                    'parse_mode': 'HTML',
                    'disable_notification': False
                }
                response = requests.post(
                    f"{self.api_url}/sendMessage",
                    json=data,
                    timeout=10
                )
            
            if response.status_code == 200:
                self.rate_limits[alert_type] = current_time
                logger.info(f"Alert sent to Telegram: {message[:50]}")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def send_batch_alerts(self, alerts: list) -> bool:
        """Send multiple alerts in a batch"""
        if not alerts:
            return True
        
        text = "🚨 <b>CCTV Alerts Summary</b>\n\n"
        for alert in alerts[:10]:  # Limit to 10 alerts
            text += f"• {alert}\n"
        
        if len(alerts) > 10:
            text += f"\n... and {len(alerts) - 10} more alerts"
        
        return self.send_alert(text, alert_type="batch")

class AlertProcessor:
    def __init__(self, bot: TelegramBot):
        self.bot = bot
        self.alert_queue = asyncio.Queue()
        self.running = True
    
    async def add_alert(self, message: str, image_path: Optional[str] = None, 
                        alert_type: str = "default"):
        await self.alert_queue.put((message, image_path, alert_type))
    
    async def process(self):
        while self.running:
            try:
                message, image_path, alert_type = await asyncio.wait_for(
                    self.alert_queue.get(), timeout=1.0
                )
                await asyncio.to_thread(
                    self.bot.send_alert, message, image_path, alert_type
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
    
    def stop(self):
        self.running = False
