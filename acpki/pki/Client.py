import sys, os, socket
from OpenSSL import SSL
from acpki.pki.CommAgent import CommAgent


class Client(CommAgent):
    def __init__(self):
        # Config
        self.private_key = "client.pkey"
        self.certificate = "client.cert"
        self.ca_certificate = "ca.cert"

        self.context = self.get_context()
