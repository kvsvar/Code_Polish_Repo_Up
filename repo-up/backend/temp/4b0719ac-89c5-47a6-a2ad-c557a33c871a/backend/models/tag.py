from backend.models.base import BaseModel

class Tag(BaseModel):
    name: str
    description: str
