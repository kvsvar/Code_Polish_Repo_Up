from backend.services.notification_service import NotificationService

def register_routes(app):
    app.add_route('/notification', lambda: "OK")
