import json


class EPG(object):
    def __init__(self, dn, name):
        """
        :param json_epg:    JSON string that represents the EPG. Not providing JSON will result in ALL attributes being
                            set to None, and hence REQUIRES calling epg.load_from_json() manually at a later point, e.g.
                            once the information is received from the APIC.
        """
        self.dn = dn
        self.name = name
        self.descr = None
        self.ap = None  # TODO: Should be taken into account

        self.provides = []
        self.consumes = []

    def equals(self, epg):
        return self.dn == epg.dn


class EPGUpdate:
    def __init__(self, dn, name, mod_ts, status, sub_id):
        self.dn = dn
        self.name = name
        self.mod_ts = mod_ts
        self.status = status
        self.sub_id = sub_id
