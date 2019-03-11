from acpki.ACIAdapter import ACIAdapter
from acpki.pki.CertificateManager import CertificateManager


class Main:
    def __init__(self):
        self.aci_adapter = None

    def run(self):
        csr = CertificateManager.create_csr(CN="127.0.0.1")
        CertificateManager.save_csr(csr, "client.csr")


if __name__ == "__main__":
    main = Main()
    main.run()
