from acpki.pki import CertificateManager
from acpki.models import CertificateRequest
import os, sys


class CA:
    def __init__(self):
        self.cert_dir = CertificateManager.get_cert_path()
        self.serial_file = "serial.txt"

    def request_certificate(self, request):
        if not isinstance(request, CertificateRequest):
            raise TypeError("Request must be of type CertificateRequest.")

    def get_next_serial(self):
        serial_path = os.path.join(self.cert_dir, self.serial_file)
        if not os.path.exists(serial_path):
            # Create file and set serial number to 10,000
            try:
                f = open(serial_path, "w")
                f.write("10000")
                f.close()
            except IOError as e:
                print("Could not create serial file: {0}".format(e))
                sys.exit(1)

        try:
            with open(serial_path, "r") as f:
                next_serial = int(f.readline()) + 1
            with open(serial_path, "w") as f:
                f.write(str(next_serial))
                return next_serial
        except IOError as e:
            print("Could not read and update serial number from file: {0}".format(e))


class RA:
    def __init__(self):
        pass


# Temporarily and for testing purposes only
if __name__ == "__main__":
    ca = CA()
    serial = ca.get_next_serial()
    print(serial)