from backend.utils.logger import Logger

class Authservice:
    def __init__(self):
        self.logger = Logger()
        
    def execute(self):
        self.logger.info("Executing auth_service")
