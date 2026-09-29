from pydantic import BaseModel as PydanticBase

class BaseModel(PydanticBase):
    id: str
    created_at: str
    updated_at: str
    
    def save(self):
        pass
