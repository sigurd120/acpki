class EP(object):
    def __init__(self, name, address=None, port=None, epg=None):
        self.name = name
        self.address = address
        self.port = port
        self.epg = epg

        self.certificates = {}

    def equals(self, ep):
        return self.name == ep.name and self.address == ep.address
