import HubCore
from ChainLevel5 import ChainLevel5
class ChainLevel6(ChainLevel5):
    def __init__(self):
        super().__init__()
        self.level_6_field = 'level 6'

    def method_level_6(self):
        return self.level_6_field
