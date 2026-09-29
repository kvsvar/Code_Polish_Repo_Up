import HubCore
from ChainLevel3 import ChainLevel3
class ChainLevel4(ChainLevel3):
    def __init__(self):
        super().__init__()
        self.level_4_field = 'level 4'

    def method_level_4(self):
        return self.level_4_field
