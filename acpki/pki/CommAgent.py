import os
from OpenSSL import SSL
from acpki.util.custom_exceptions import ConfigError
from acpki.pki.CertificateManager import CertificateManager


class CommAgent:
    """
    A CommAgent is a class that includes common functionality for the Client and Server classes, both of which extends
    this class.
    """
    def __init__(self):
        self.private_key = None
        self.certificate = None
        self.ca_certificate = None

        self.client_addr = "127.0.0.1"
        self.client_port = 13150
        self.serv_addr = "127.0.0.1"
        self.serv_port = 13151

    def get_context(self):
        """
        Get the communication context based on the agent's configuration.
        :return:            OpenSSL Context object
        """
        if self.private_key is None or self.certificate is None or self.ca_certificate is None:
            raise ConfigError("Values for private key, certificate and CA certificate are required!")
        context = SSL.Context(SSL.TLSv1_2_METHOD)   # TODO: Find out if TLS 1.3 is available in new version of PyOpenSSL
        context.set_verify(SSL.VERIFY_PEER, self.ssl_verify_cb)
        context.use_privatekey_file(self.get_cert_path(self.private_key))
        context.use_certificate_file(self.get_cert_path(self.certificate))
        context.load_verify_locations(self.get_cert_path(self.ca_certificate))
        return context

    @staticmethod
    def ssl_verify_cb(conn, cert, err_num, depth, ok):
        """
        SSL verification callback method.
        :param conn:        Connection object
        :param cert:        X.509 certificate object
        :param err_num:     Number of errors
        :param depth:       Error depth
        :param ok:          Return code
        :return:            True if there are no errors, False otherwise
        """
        return err_num == 0

    @staticmethod
    def get_cert_path(file_name=None):
        """
        Join the base certificates directory with the file name.
        :param file_name:   The file name of the certificate
        :return:
        """
        if file_name is None:
            return CertificateManager.certs_dir
        else:
            return os.path.join(CertificateManager.certs_dir, file_name)
