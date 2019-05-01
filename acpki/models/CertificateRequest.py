from acpki.models import EP


class CertificateRequest(object):
    def __init__(self, origin, destination, csr):
        self.client = origin
        self.server = destination
        self.csr = csr

    def equals(self, request):
        return self.client.equals(request.origin) and self.server.equals(request.destination)


class CertificateValidationRequest(object):
    def __init__(self, client, server, certificate):
        self.client = client
        self.server = server
        self.cert = certificate

    def get_errors(self):
        if self.client is None or self.server is None or self.cert is None:
            return "Invalid CVR. One or more required attributes were None. "
        if not isinstance(self.client, EP) or not isinstance(self.server, EP):
            return "Client or Server attribute was not of type EP. "
