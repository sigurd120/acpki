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

    def revoke_certificate(self, serial_number):
        if self.is_revoked(serial_number):
            print("Certificate \"{0}\" is already revoked.".format(serial_number))
            return None
        try:
            revoked_file = open(self.revoked_file_path, "a")
            revoked_file.write(serial_number + '\n')
        except IOError as e:
            print("Could not revoke certificate: " + e)
        else:
            print("Certificate \"{0}\" was revoked successfully.".format(serial_number))
        finally:
            revoked_file.close()

    def unrevoke_certificate(self, serial_number):
        # TODO: Implement this method
        pass

    def is_revoked(self, serial_number):
        revoked_file = open(self.revoked_file_path, "r")
        for line in revoked_file:
            if line.strip() == serial_number:
                return True
        return False


# Testing purposes only
if __name__ == "__main__":
    ocsp_responder = OCSPResponder()
    ocsp_responder.revoke_certificate("blablablabla")
    ocsp_responder.revoke_certificate("fdsadfsaksks")
    ocsp_responder.revoke_certificate("dsaklklsdkdj")
    ocsp_responder.revoke_certificate("blablablabfd")
    if ocsp_responder.is_revoked("blablablabla"):
        print("Certificate is revoked.")
    else:
        print("Certificate is not revoked. Lucky you!")