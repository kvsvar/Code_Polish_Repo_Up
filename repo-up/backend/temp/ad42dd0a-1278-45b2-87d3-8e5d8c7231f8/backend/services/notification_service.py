from backend.models.notification import Notification
from backend.services.audit_service import AuditService
from backend.utils.logger import Logger

class NotificationService:
    def __init__(self):
        self.audit = AuditService()
        self.logger = Logger()
        
    def notify_task_created(self, task):
        n = Notification(name="Task Created", description=task.title, id="1", created_at="now", updated_at="now")
        self.audit.log_notification(n)
        self.logger.info("Notification sent")
