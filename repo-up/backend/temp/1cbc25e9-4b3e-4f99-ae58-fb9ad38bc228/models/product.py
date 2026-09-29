from models.generic import GenericModel
class Product(GenericModel):
    def __init__(self, id, name):
        self.id = id
        self.name = name
