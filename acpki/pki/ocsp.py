from acpki.pki import CertificateManager
import os


class OCSPResponder:
    """
    This class represents a simple OCSP responder. It will look a certificate serial number up in a simple text file
    containing all revoked certificates, and refuse certificates found in the file.
    """
    def __init__(self):
        self.revoked_file_path = os.path.join(CertificateManager.get_cert_path(), "revoked.txt")

        # Create the file if it does not exist
        try:
            if not os.path.exists(self.revoked_file_path):
                revoked_file = open(self.revoked_file_path, "w")
                revoked_file.close()
        except IOError:
            self.revoked_file_path = None
            print("Error: OCSP responder could not be initiated.")

    def revoke_serial(self, serial_number):
        if self.is_revoked(serial_number):
            print("Certificate \"{0}\" is already revoked.".format(serial_number))
            return None
        try:
            revoked_file = open(self.revoked_file_path, "a")
            revoked_file.write(serial_number + '\n')
            revoked_file.close()
        except IOError as e:
            print("Could not revoke certificate: {0}".format(e))
        else:
            print("Certificate \"{0}\" was revoked successfully.".format(serial_number))

    def revoke_certificate(self, certificate):
        self.revoke_serial(certificate.get_serial_number())

    def unrevoke_serial(self, serial_number):
        found = False
        try:
            with open(self.revoked_file_path, "r+") as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if line.strip() != serial_number:
                        f.write(line)
                    else:
                        found = True
                f.truncate()
        except IOError as e:
            print("Error: Could not unrevoke certificate \"{0}\": {1}".format(serial_number, e))

        if found:
            print("Successfully unrevoked the certificate \"{0}\"".format(serial_number))
        return found

    def unrevoke_certificate(self, certificate):
        self.unrevoke_serial(certificate.get_serial_number())

    def is_revoked(self, serial_number):
        revoked_file = open(self.revoked_file_path, "r")
        for line in revoked_file:
            if line.strip() == serial_number:
                return True
        return False
