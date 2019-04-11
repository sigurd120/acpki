import json


class AP:
    def __init__(self, name):
        self.name = name

    def to_json(self):
        obj = {
            "fvAp": {
                "attributes": {
                    "name": self.name
                }
            }
        }
        return json.dumps(obj)