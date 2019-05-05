from acpki.models import EP


class CertificateRequest(object):
    def __init__(self, origin, destination, csr):
        self.origin = origin
        self.destination = destination
        self.csr = csr

    def equals(self, request):
        return self.origin.equals(request.origin) and self.destination.equals(request.destination)


class CertificateValidationRequest(object):
    def __init__(self, client, server, certificate):
        self.origin = client
        self.destination = server
        self.cert = certificate