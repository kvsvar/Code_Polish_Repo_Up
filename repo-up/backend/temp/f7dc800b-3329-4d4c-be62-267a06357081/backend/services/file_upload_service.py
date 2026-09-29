import os
from backend.utils.logger import Logger

class FileUploadService:
    def __init__(self):
        self.logger = Logger()
        
    def upload_file(self, filename, content):
        # Missing try/except for file I/O
        with open(filename, 'w') as f:
            f.write(content)
        self.logger.info("File uploaded")
