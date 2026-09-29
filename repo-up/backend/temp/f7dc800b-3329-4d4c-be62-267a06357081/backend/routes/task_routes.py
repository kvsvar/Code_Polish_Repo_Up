from backend.services.task_service import TaskService

def register_routes(app):
    app.add_route('/task', lambda: "OK")
