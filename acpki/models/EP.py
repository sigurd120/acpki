class EP:
    def __init__(self, name, address, epg, dns=None):
        self.name = name
        self.address = address
        self.epg = epg
        self.dns = dns

        self.certificates = {}

    def equals(self, ep):
        return self.name == ep.name and self.address == ep.address
