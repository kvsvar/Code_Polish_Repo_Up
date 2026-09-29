from backend.models.soft_delete import SoftDeleteModel
from backend.models.user import User
from backend.models.project import Project

class Task(SoftDeleteModel):
    title: str
    description: str
    status: str
    assignee_id: str
    project_id: str
    
    def assign_to(self, user: User):
        self.assignee_id = user.id
