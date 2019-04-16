class CertificateRequest(object):
    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination

        self.issue = False
        self.cert = None  # TODO: Will be used to check a certificate against Cisco ACI
