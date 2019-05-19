import uuid
from acpki.pki import CertificateManager, OCSPResponder
from acpki.models import CertificateRequest, CertificateValidationRequest
from acpki.psa import PSA
from acpki.config import CONFIG
from acpki.util.exceptions import RequestError
from OpenSSL import crypto


class RA:
    """
    The Registration Authority (RA) is responsible for issuing certificates to endpoints who are allowed to communicate.
    """
    def __init__(self, ca, psa):
        # Arguments
        self.ca = ca
        self.psa = psa
        self.cert = None
        self.verbose = CONFIG["verbose"]

        # Config
        self.cert_dir = CertificateManager.get_cert_path()
        self.default_key_type = crypto.TYPE_RSA
        self.default_key_size = 2048
        self.organisation = "Corporation Ltd"

        self.setup()

    def setup(self):
        """
        Configure the RA with its own certificates.
        :return:
        """
        if CertificateManager.cert_file_exists("ra.cert"):
            # Certificate exists
            self.cert = CertificateManager.load_cert("ra.cert")
        else:
            # Not found, create new certificate for the RA
            if self.verbose:
                print("Generating new RA certificate.")

            if self.ca is None or not isinstance(self.ca, CA):
                raise ValueError("The \"ca\" field must be defined and instance of CA to setup an RA.")

            # Create certificate own certificate on behalf of the CA
            keys = CertificateManager.create_key_pair(self.default_key_type, self.default_key_size)
            csr = CertificateManager.create_csr(keys, C="NO", ST="Oslo", L="Oslo", O=self.organisation, OU="RA",
                                                CN="RA")
            issuer = self.ca.get_root_certificate().get_issuer()  # Issuer of root certificate (i.e. root CA)
            cert = CertificateManager.create_cert(csr, self.get_next_serial(), issuer, self.ca.get_keys(), ca=True)

            # Save certificate, keys and files
            CertificateManager.save_cert(cert, CONFIG["pki"]["ra-cert-name"])
            CertificateManager.save_pkey(keys, CONFIG["pki"]["ra-pkey-name"])
            self.cert = cert

    def request_certificate(self, request):
        """
        This method checks if a certificate is allowed by the PSA and issues it if that is the case. The RA currently
        issues certificates using the CA key for simplicity. The RA could have its own key with signing permission (i.e.
        the ca flag set to true) and use that instead.
        :param request:     CertificateRequest object (AC-PKI model)
        :return:            Certificate or None
        """
        # Validate request type
        if not isinstance(request, CertificateRequest):
            raise RequestError("Certificate request invalid. Must be of type CertificateRequest!")

        # Check if connection is allowed
        if self.psa.connection_allowed(request.origin, request.destination):
            # Connection allowed
            ou = self.register_ou((request.origin.epg.name, request.destination.epg.name))
            subject = request.csr.get_subject()

            # Override attributes in the CSR (if they are defined)
            setattr(subject, "C", "NO")
            setattr(subject, "ST", "Oslo")
            setattr(subject, "L", "Oslo")
            setattr(subject, "O", "AC-PKI Corp")
            setattr(subject, "OU", ou)
            setattr(subject, "CN", request.origin.name)

            crt = CertificateManager.create_cert(request.csr, self.get_next_serial(), self.ca.get_issuer(),
                                                 self.ca.get_keys())

            return crt
        else:
            # Connection not allowed
            print("Connection not allowed between {0} and {1}. Certificate refused."
                  .format(request.origin, request.destination))
            return None

    def register_ou(self, eps):
        """
        Generate an OU reference for any given certificate. This will be used as a reference to that particular pair of
        EPGs when validating certificates in the CA. Outsourced to the PSA.
        :param eps:     Tuple containing (origin, destination) EPs
        :return:        The OU (key) with which the request was registered
        """
        return self.psa.register_ou(eps)

    @staticmethod
    def get_next_serial():
        """
        Generates a random 64 bit serial number for certificates.
        :return:    Serial number
        """
        return uuid.uuid1().int >> 64  # Get the first 64 bits of the random output


class CA:
    """
    The Certification Authority (CA) is responsible for validating certificates, as well as keeping the highest
    certificate in the PKI hierarchy along with its corresponding keys.
    PLEASE NOTE: This implementation is genuinely insecure, as the system is only a proof-of-concept. Anyone with a
    reference to a CA can directly request the private key and sign certificates acting like a CA. It is only developed
    to look and act similarly to the architecture of a realistic CA implementation.
    """
    def __init__(self, psa):
        self.root_cert = self.get_root_certificate()
        self.keys = self.get_keys()  # Must be called after get_root_certificate() to ensure synchronised
        self.psa = psa
        self.ra = RA(self, self.psa)
        self.ocsp_responder = OCSPResponder()

    def validate_cert(self, cvr):
        """
        This method validates a certificate validation request (CVR) with the PSA. The certificate will be approved only
        if the certificate matches the records of the PSA and has not been revoked.
        :param cvr:     Certificate validation request (instance of CertificateValidationRequest class)
        :return:        The result of the certificate validation
        """
        return self.psa.validate_certificate(cvr)

    def get_issuer(self):
        """
        Get the issuer object for the CA
        :return:
        """
        return self.root_cert.get_issuer()

    def get_ra(self):
        """
        Get the RA associated with this CA
        """
        return self.ra

    def get_ocsp_responder(self):
        """
        Get the OCSP responder associated with this CA
        """
        return self.ocsp_responder

    @staticmethod
    def get_root_certificate():
        """
        Get the certificate for the root CA
        :return:
        """
        if CertificateManager.cert_file_exists(CONFIG["pki"]["ca-cert-name"]):
            # Certificate exists
            return CertificateManager.load_cert(CONFIG["pki"]["ca-cert-name"])
        else:
            # Create CA certificate
            pkey = CertificateManager.create_key_pair()
            csr = CertificateManager.create_csr(pkey, O="AC-PKI", OU="CA", C="NO", ST="Oslo", L="Oslo",
                                                CN="Root CA")
            cert = CertificateManager.create_self_signed_cert(csr, pkey, RA.get_next_serial())

            # Save files and return
            CertificateManager.save_pkey(pkey, CONFIG["pki"]["ca-pkey-name"])
            CertificateManager.save_cert(cert, CONFIG["pki"]["ca-cert-name"])

            return cert

    @staticmethod
    def get_keys():
        pkey_name = CONFIG["pki"]["ca-pkey-name"]
        if CertificateManager.cert_file_exists(pkey_name):
            return CertificateManager.load_pkey(pkey_name)


# Temporarily and for testing purposes only
if __name__ == "__main__":
    psa = PSA()
    ca = CA(psa)
    ra = ca.get_ra()
    serial = ra.get_next_serial()
    print(serial)