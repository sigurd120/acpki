import json


class EPG:
    def __init__(self, json_epg=None):
        """
        :param json_epg:    JSON string that represents the EPG. Not providing JSON will result in ALL attributes being
                            set to None, and hence REQUIRES calling epg.load_from_json() manually at a later point, e.g.
                            once the information is received from the APIC.
        """
        self.name = None
        self.descr = None
        self.dn = None

        self.ready = False

        if json_epg is not None:
            self.load_from_json(json_epg)

    def load_from_json(self, json_epg):
        """
        Load EPG from a JSON string, as received from the APIC.
        :param json_epg:
        :return:
        """
        jsn = json.loads(json_epg)
        self.name = jsn["name"]
        self.descr = jsn["descr"]
        self.dn = jsn["dn"]

        self.ready = True
