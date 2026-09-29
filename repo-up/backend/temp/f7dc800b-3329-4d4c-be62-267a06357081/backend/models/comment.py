from backend.models.base import BaseModel
from backend.models.task import Task
from backend.models.user import User

class Comment(BaseModel):
    task_id: str
    author_id: str
    content: str
