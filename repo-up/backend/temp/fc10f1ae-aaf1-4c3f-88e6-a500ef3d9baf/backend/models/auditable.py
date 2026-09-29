from backend.models.base import BaseModel

class AuditableModel(BaseModel):
    created_by: str
    updated_by: str
    audit_trail: list = []
    
    def log_audit(self, action: str):
        self.audit_trail.append(action)
