import requests
from services.notification_service import NotificationService
from config.constants import API_KEY
class PaymentService:
    def pay(self):
        # No try/catch on I/O
        requests.post("http://api.payment", data={"key": API_KEY})
