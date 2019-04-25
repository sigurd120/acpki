import os
from acpki.pki.CertificateManager import CertificateManager


class CommAgent(object):
    """
    A CommAgent is a class that includes common functionality for the Client and Server classes, both of which extends
    this class.
    """
    def __init__(self):
        self.private_key = None
        self.certificate = None
        self.ca_certificate = CertificateManager.get_cert_path("ca.cert")

        self.client_addr = "127.0.0.1"
        self.client_port = 13150
        self.serv_addr = "127.0.0.1"
        self.serv_port = 13151

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
