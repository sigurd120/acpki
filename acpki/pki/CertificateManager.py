import sys
from OpenSSL import crypto as crypto
from OpenSSL import SSL


class CertificateManager:
    """
    This class will handle common tasks like verifying, creating or signing certificates. The class is partly based on
    the examples provided in pyOpenSSL.
    """
    default_validity = 31536000  # One year (3600 * 24 * 365)

    def __init__(self):
        pass

    @staticmethod
    def create_csr(digest="md5", **attributes):
        """
        Generates a default type
        :param digest:          Digest hashing algorithm. Default: "md5"
        :param attributes:      Attributes to apply on the CSR. Valid params: C, ST, L, O, OU and CN
        :return:
        """
        public_key = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
        csr = crypto.X509Req()
        subject = csr.get_subject()

        for (key, val) in attributes:
            if key in ["C", "ST", "L", "O", "OU", "CN"]:
                setattr(subject, key, val)
            else:
                raise ValueError("Invalid attribute provided for CSR. Permitted keys: C, ST, L, O, OU and CN.")

        csr.set_pubkey(public_key)
        csr.sign(public_key, digest)

        return csr

    @staticmethod
    def create_cert(csr, serial_number, issuer_cert, issuer_key, not_before=0, not_after=default_validity,
                    digest="md5"):
        """
        :param csr:             The certificate signing request (CSR) on which to base the certificate.
        :param serial_number:   Serial number to apply for the certificate.
        :param issuer_cert:     Certificate for the party issuing the certificate (typically CA or RA certificate).
        :param issuer_key:      Private key for the issuer.
        :param not_before:      Seconds from now when certificate should become valid.
        :param not_after:       Seconds from now when certificate should become invalid.
        :param digest:          Digest hashing algorithm. Default: "md5"
        :return:                The certificate that was just created. None if creation failed.
        """
        cert = crypto.X509()
        cert.set_serial_number(serial_number)
        cert.gmtime_adj_notBefore(not_before)
        cert.gmtime_adj_notAfter(not_after)
        cert.set_issuer(issuer_cert.getSubject())
        cert.set_pubkey(csr.get_pubkey())
        cert.sign(issuer_key, digest)
        return cert

    @staticmethod
    def create_self_signed_cert(csr, private_key, serial_number, not_before=0, not_after=default_validity,
                                digest="md5"):
        """

        :param csr:             The certificate signing request (CSR) on which to base the certificate.
        :param private_key:     Private key that corresponds with the CSR public key.
        :param serial_number:   Serial number to apply for the certificate.
        :param not_before:      Seconds from now when certificate should become valid.
        :param not_after:       Seconds from now when certificate should become invalid.
        :param digest:          Digest hashing algorithm. Default: "md5"
        :return:                The certificate that was just created. None if creation failed.
        """
        cert = crypto.X509()
        cert.set_serial_number(serial_number)
        cert.gmtime_adj_notBefore(not_before)
        cert.gmtime_adj_notAfter(not_after)
        cert.set_issuer(csr.get_subject)
        cert.set_pubkey(csr.get_pubkey())
        cert.sign(private_key, digest)
        return cert

    @staticmethod
    def create_key_pair(key_type, key_size):
        """
        Generate a key pair for certificate generation.
        :param key_type:        Valid key type, either crypto.TYPE_RSA or crypto.TYPE_DSA
        :param key_size:        Key size that is valid with respect to key type, e.g. 2048 for TYPE_RSA.
        :return:                The key pair that was generated.
        """
        pkey = crypto.Pkey()
        pkey.generate_key(key_type, key_size)
        return pkey
