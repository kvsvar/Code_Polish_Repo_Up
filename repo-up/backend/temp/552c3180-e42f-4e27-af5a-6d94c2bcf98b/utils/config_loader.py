class ConfigLoader:
    def load(self, dynamic_str):
        # Dangerous function
        eval(dynamic_str)
