import requests
from backend.utils.logger import Logger

class WebhookService:
    def __init__(self):
        self.logger = Logger()
        self.webhook_secret = "token='a1b2c3d4e5f6g7h8i9j0'" # Another secret
        
    def trigger(self, url, payload):
        # Missing try/except for network I/O
        res = requests.post(url, json=payload)
        self.logger.info(f"Webhook triggered: {res.status_code}")
