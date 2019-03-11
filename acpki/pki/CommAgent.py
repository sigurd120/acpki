import sys, os, socket
from OpenSSL import SSL
from acpki.util.custom_exceptions import ConfigError


class CommAgent:
    def __init__(self):
        self.private_key = None
        self.certificate = None
        self.ca_certificate = None

    def get_context(self):
        if self.private_key is None or self.certificate is None or self.ca_certificate is None:
            raise ConfigError("Values for private key, certificate and CA certificate are required!")
        context = SSL.Context(SSL.TLSv1_2_METHOD)
        context.set_verify(SSL.VERIFY_PEER, self.ssl_verify_cb)
        context.use_privatekey_file(self.get_cert_path(self.private_key))
        context.use_certificate_file(self.get_cert_path(self.certificate))
        context.load_verify_locations(self.get_cert_path(self.ca_certificate))
        return context

    @staticmethod
    def ssl_verify_cb(conn, cert, err_num, depth, ok):
        return err_num == 0

    @staticmethod
    def get_cert_path(name):
        cert_dir = os.path.join(os.curdir, "certs")
        cert_path = os.path.join(cert_dir, name)
        return cert_path
