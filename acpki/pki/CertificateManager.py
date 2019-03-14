import os
from OpenSSL import crypto


class CertificateManager:
    """
    This class will handle common tasks like verifying, creating or signing certificates. The class is partly based on
    the examples provided in pyOpenSSL.
    """
    default_validity = 31536000  # One year (3600 * 24 * 365)
    certs_dir = os.path.abspath("./certs")  # Relative to pki directory

    def __init__(self):
        pass

    @staticmethod
    def create_csr(key_pair, digest="md5", **attributes):
        """
        Generates a certificate signing request (CSR) with the default encryption type and key size.
        :param digest:          Digest hashing algorithm. Default: "md5"
        :param attributes:      Attributes to apply on the CSR. Valid params: C, ST, L, O, OU and CN
        :return:
        """
        # public_key = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
        csr = crypto.X509Req()
        subject = csr.get_subject()

        for (key, val) in attributes.items():
            if key in ["C", "ST", "L", "O", "OU", "CN"]:
                setattr(subject, key, val)
            else:
                raise ValueError("Invalid attribute provided for CSR. Permitted keys: C, ST, L, O, OU and CN.")

        csr.set_pubkey(key_pair)
        csr.sign(key_pair, digest)

        return csr

    @staticmethod
    def create_cert(csr, serial_number, issuer, issuer_key, ca=False, not_before=0, not_after=default_validity,
                    digest="sha256"):
        """
        Generate a certificate based on the provided certificate signing request (CSR).
        :param csr:             The CSR on which to base the certificate.
        :param serial_number:   Serial number to apply for the certificate.
        :param issuer:          The subject issuing the certificate
        :param issuer_key:      Private key for the issuer.
        :param ca               Certificate is issued to a CA (boolean)
        :param not_before:      Seconds from now when certificate should become valid.
        :param not_after:       Seconds from now when certificate should become invalid.
        :param digest:          Digest hashing algorithm. Default: "md5"
        :return:                The certificate that was just created. None if creation failed.
        """
        cert = crypto.X509()
        cert.set_serial_number(serial_number)
        cert.set_subject(csr.get_subject())
        cert.gmtime_adj_notBefore(not_before)
        cert.gmtime_adj_notAfter(not_after)
        cert.set_issuer(issuer)
        cert.set_pubkey(csr.get_pubkey())

        if ca:
            cert.add_extensions([
                crypto.X509Extension(b"basicConstraints", True, b"CA:true,pathlen:1"),
                crypto.X509Extension(b"keyUsage", True, b"keyCertSign"),
                crypto.X509Extension(b"extendedKeyUsage", False, b"clientAuth,serverAuth")
            ])
        else:
            cert.add_extensions([
                crypto.X509Extension(b"extendedKeyUsage", False, b"clientAuth,serverAuth")
            ])

        cert.sign(issuer_key, digest)

        return cert

    @staticmethod
    def create_self_signed_cert(csr, private_key, serial_number, not_before=0, not_after=default_validity,
                                digest="sha256"):
        """
        Generate a self signed certificate for the root CA.
        :param csr:             The certificate signing request (CSR) on which to base the certificate.
        :param private_key:     Private key that corresponds with the CSR public key.
        :param serial_number:   Serial number to apply for the certificate.
        :param not_before:      Seconds from now when certificate should become valid.
        :param not_after:       Seconds from now when certificate should become invalid.
        :param digest:          Digest hashing algorithm. Default: "md5"
        :return:                The certificate that was just created. None if creation failed.
        """
        return CertificateManager.create_cert(csr, serial_number, csr.get_subject(), private_key, True, not_before,
                                              not_after, digest)

    @staticmethod
    def get_cert_path(file_name):
        return os.path.join(CertificateManager.certs_dir, file_name)

    @staticmethod
    def cert_file_exists(file_name):
        return os.path.isfile(CertificateManager.get_cert_path(file_name))

    @staticmethod
    def create_key_pair(key_type, key_size):
        """
        Generate a key pair for certificate generation.
        :param key_type:        Valid key type, either crypto.TYPE_RSA or crypto.TYPE_DSA
        :param key_size:        Key size that is valid with respect to key type, e.g. 2048 for TYPE_RSA.
        :return:                The key pair that was generated.
        """
        pkey = crypto.PKey()
        pkey.generate_key(key_type, key_size)
        return pkey

    @staticmethod
    def save_csr(csr, file_name):
        """
        Save a certificate signing request (CSR) to the certificates directory with the file name provided.
        :param csr:             The CSR as generated by CertificateManager.py
        :param file_name:       The name to which the file should be saved
        :return:
        """
        file_path = os.path.join(CertificateManager.certs_dir, file_name)
        print("Saving CSR file to " + file_path)
        open(file_path, "w").write((crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr)))

    @staticmethod
    def save_cert(cert, file_name):
        """
        Save an X.509 certificate to the certificates directory with the file name provided.
        :param cert:            Certificate generated by CertificateManager.py
        :param file_name:       File name to which the file should be saved
        :return:
        """
        file_path = os.path.join(CertificateManager.certs_dir, file_name)
        print("Saving certificate to {0}".format(file_path))
        open(file_path, "w").write((crypto.dump_certificate(crypto.FILETYPE_PEM, cert)))

    @staticmethod
    def save_pkey(pkey, file_name):
        """
        Save the private key to the certificates directory with the file name provided.
        :param pkey:            Private key generated by CertificateManager.py
        :param file_name:       File name to which the private key should be saved
        :return:
        """
        file_path = os.path.join(CertificateManager.certs_dir, file_name)
        print("Saving private key to " + file_path)
        open(file_path, "w").write((crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)))

    @staticmethod
    def load_cert(file_name):
        cert_file = open(CertificateManager.get_cert_path(file_name), "rt").read()
        return crypto.load_certificate(crypto.FILETYPE_PEM, cert_file)

    @staticmethod
    def load_pkey(file_name):
        pkey_file = open(CertificateManager.get_cert_path(file_name), "rt").read()
        return crypto.load_privatekey(crypto.FILETYPE_PEM, pkey_file)
