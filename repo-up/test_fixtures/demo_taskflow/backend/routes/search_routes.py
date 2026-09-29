from backend.services.search_service import SearchService

def register_routes(app):
    app.add_route('/search', lambda: "OK")
