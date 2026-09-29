from backend.services.audit_service import AuditService

def register_routes(app):
    app.add_route('/audit', lambda: "OK")
