from backend.services.project_service import ProjectService

def register_routes(app):
    app.add_route('/project', lambda: "OK")
