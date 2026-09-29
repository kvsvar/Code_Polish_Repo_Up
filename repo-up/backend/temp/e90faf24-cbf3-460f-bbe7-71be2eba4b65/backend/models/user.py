from backend.models.soft_delete import SoftDeleteModel

class User(SoftDeleteModel):
    username: str
    email: str
    password_hash: str
