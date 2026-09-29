from backend.models.task import Task
from backend.services.notification_service import NotificationService
from backend.utils.logger import Logger

class TaskService:
    def __init__(self):
        self.logger = Logger()
        self.notif_service = NotificationService()
        
    def create_task(self, data):
        task = Task(**data)
        self.notif_service.notify_task_created(task)
        self.logger.info(f"Task created: {task.id}")
        return task
