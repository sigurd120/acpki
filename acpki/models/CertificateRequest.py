class CertificateRequest(object):
    def __init__(self, origin, destination):
        self.client = origin
        self.server = destination

    def equals(self, request):
        return self.client.equals(request.origin) and self.server.equals(request.destination)
