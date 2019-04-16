from acpki.pki import CertificateManager
from acpki.models import CertificateRequest
from acpki.psa import PSA
from acpki.config import CONFIG
import os, sys


class RA:
    def __init__(self, psa, ca):
        # Arguments
        self.psa = psa
        self.ca = ca

        # Config
        self.cert_dir = CertificateManager.get_cert_path()
        self.serial_file = "serial.txt"

    def certificate_request(self, request):
        # Check if connection is allowed
        if not self.psa.connection_allowed(request.origin, request.destination):
            print("Connection not allowed between {0} and {1}. Certificate refused."
                  .format(request.origin, request.destination))
            return None

        # Issue certificate


    # TODO: This method should probably be removed. Automatically generate serial instead! 64 bit secure random...
    #       No check should be required.
    @staticmethod
    def get_next_serial():
        cert_dir = CertificateManager.get_cert_path()
        serial_path = os.path.join(CONFIG["pki"]["cert-dir"], "serial.txt")
        if not os.path.exists(serial_path):
            # Create file and set serial number to 10,000
            try:
                f = open(serial_path, "w")
                f.write("10000")
                f.close()
            except IOError as e:
                print("Could not create serial file: {0}".format(e))
                sys.exit(1)

        # Update serial number
        try:
            with open(serial_path, "r") as f:
                next_serial = int(f.readline()) + 1
            with open(serial_path, "w") as f:
                f.write(str(next_serial))
                return int(next_serial)
        except IOError as e:
            print("Could not read and update serial number from file: {0}".format(e))


class CA:
    def __init__(self):
        self.root_cert = self.get_root_certificate()

    @staticmethod
    def get_root_certificate():
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


# Temporarily and for testing purposes only
if __name__ == "__main__":
    psa = PSA()
    ca = CA()
    ra = RA(psa, ca)
    serial = ra.get_next_serial()
    print(serial)