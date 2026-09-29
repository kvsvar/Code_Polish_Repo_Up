from backend.services.user_service import UserService

def register_routes(app):
    app.add_route('/user', lambda: "OK")
