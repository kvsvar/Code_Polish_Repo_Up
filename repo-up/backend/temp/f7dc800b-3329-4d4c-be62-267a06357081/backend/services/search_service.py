from backend.utils.logger import Logger

class Searchservice:
    def __init__(self):
        self.logger = Logger()
        
    def execute(self):
        self.logger.info("Executing search_service")
