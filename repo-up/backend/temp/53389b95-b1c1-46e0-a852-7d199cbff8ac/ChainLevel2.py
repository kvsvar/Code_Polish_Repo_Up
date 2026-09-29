import HubCore
from ChainLevel1 import ChainLevel1
class ChainLevel2(ChainLevel1):
    def __init__(self):
        super().__init__()
        self.level_2_field = 'level 2'

    def method_level_2(self):
        return self.level_2_field
