import HubCore
from ChainLevel4 import ChainLevel4
class ChainLevel5(ChainLevel4):
    def __init__(self):
        super().__init__()
        self.level_5_field = 'level 5'

    def method_level_5(self):
        return self.level_5_field
