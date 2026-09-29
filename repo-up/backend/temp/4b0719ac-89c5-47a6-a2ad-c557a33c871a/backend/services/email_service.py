from backend.utils.logger import Logger
import smtplib

class EmailService:
    def __init__(self):
        self.logger = Logger()
        self.api_key = "AKIAIOSFODNN7EXAMPLE" # Hardcoded AWS key
        
    def send_email(self, to, subject, body):
        self.logger.info(f"Sending email to {to}")
        try:
            # IO operation WITH error handling
            pass
        except Exception as e:
            self.logger.error(str(e))
