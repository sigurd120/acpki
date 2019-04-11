import json


class Tenant:
    def __init__(self, name):
        self.name = name

    def to_json(self):
        obj = {
            "fvTenant": {
                "attributes": {
                    "name": self.name
                }
            }
        }

        return json.dumps(obj)
