from backend.models.audit_log import AuditLog
from backend.services.task_service import TaskService
from backend.utils.logger import Logger

class AuditService:
    def __init__(self):
        self.task_service = TaskService()  # Circular dependency
        self.logger = Logger()
        
    def log_notification(self, notif):
        # might need to fetch task details
        self.logger.info("Logging notification")
