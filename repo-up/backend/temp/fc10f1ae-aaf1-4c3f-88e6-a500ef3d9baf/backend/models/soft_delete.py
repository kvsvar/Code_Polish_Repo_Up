from backend.models.auditable import AuditableModel

class SoftDeleteModel(AuditableModel):
    is_deleted: bool = False
    deleted_at: str = None
    
    def delete(self):
        self.is_deleted = True
