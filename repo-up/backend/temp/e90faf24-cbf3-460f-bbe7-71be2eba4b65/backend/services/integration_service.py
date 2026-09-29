from backend.utils.logger import Logger

class IntegrationService:
    def __init__(self):
        self.logger = Logger()
        
    def load_dynamic_plugin(self, plugin_code):
        self.logger.info("Loading plugin dynamically")
        # Dangerous eval
        eval(plugin_code)
