import HubCore
from ChainLevel2 import ChainLevel2
class ChainLevel3(ChainLevel2):
    def __init__(self):
        super().__init__()
        self.level_3_field = 'level 3'

    def method_level_3(self):
        return self.level_3_field
