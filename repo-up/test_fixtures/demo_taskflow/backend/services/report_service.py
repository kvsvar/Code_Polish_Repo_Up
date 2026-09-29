from backend.utils.logger import Logger

class Reportservice:
    def __init__(self):
        self.logger = Logger()
        
    def execute(self):
        self.logger.info("Executing report_service")
