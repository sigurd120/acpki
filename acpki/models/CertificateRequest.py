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

    def get_errors(self):
        if self.origin is None or self.destination is None or self.cert is None:
            return "Invalid CVR. One or more required attributes were None. "
        if not isinstance(self.origin, EP) or not isinstance(self.destination, EP):
            return "Client or Server attribute was not of type EP. "
