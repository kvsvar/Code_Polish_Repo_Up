from backend.models.soft_delete import SoftDeleteModel
from backend.models.user import User

class Project(SoftDeleteModel):
    name: str
    owner_id: str
