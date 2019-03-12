from OpenSSL import crypto
from acpki.pki import Server, Client, CertificateManager


class Main:
    def __init__(self):
        self.aci_adapter = None

        self.ca_cert = None
        self.client_cert = None
        self.server_cert = None
        self.setup_completed = False

        self.client = None
        self.server = None

    def run(self):
        # Set up certificates, client and server
        self.initial_setup()
        self.server = Server()
        self.client = Client()

    def initial_setup(self):
        """
        This loads the required certificates from the files in the certs/ directory. If the files do not exist, it
        creates them using CertificateManager and saves the files for future use.
        """
        print("Setting up certificates...")

        # Create CA certificate
        if CertificateManager.cert_file_exists("ca.cert") and CertificateManager.cert_file_exists("ca.pkey"):
            print("Loading existing CA certificate from file")
            ca_cert = CertificateManager.load_cert("ca.cert")
            ca_key_pair = CertificateManager.load_pkey("ca.pkey")
        else:
            print("Generating CA certificate")
            ca_key_pair = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
            csr = CertificateManager.create_csr(ca_key_pair, C="NO", ST="Oslo", O="Corp", OU="Blab")
            ca_cert = CertificateManager.create_self_signed_cert(csr, ca_key_pair, 0)
            CertificateManager.save_pkey(ca_key_pair, "ca.pkey")
            CertificateManager.save_cert(ca_cert, "ca.cert")

        # Create client certificate
        if CertificateManager.cert_file_exists("client.cert") and CertificateManager.cert_file_exists("client.pkey"):
            print("Loading existing client certificate from file")
            client_cert = CertificateManager.load_cert("client.cert")
        else:
            print("Generating client certificate")
            client_key_pair = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
            csr = CertificateManager.create_csr(client_key_pair, C="NO", ST="Oslo", O="Corp", OU="abc123")
            client_cert = CertificateManager.create_cert(csr, 1, ca_cert, ca_key_pair)
            CertificateManager.save_cert(client_cert, "client.cert")
            CertificateManager.save_pkey(client_key_pair, "client.pkey")

        # Create server certificate
        if CertificateManager.cert_file_exists("server.cert") and CertificateManager.cert_file_exists("server.pkey"):
            print("Loading existing server certificate from file")
            server_cert = CertificateManager.load_cert("server.cert")
        else:
            print("Generating server certificate")
            server_key_pair = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
            csr = CertificateManager.create_csr(server_key_pair, C="NO", ST="Oslo", O="Corp", OU="abc321")
            server_cert = CertificateManager.create_cert(csr, 1, ca_cert, ca_key_pair)
            CertificateManager.save_cert(server_cert, "server.cert")
            CertificateManager.save_pkey(server_key_pair, "server.pkey")

        self.ca_cert = ca_cert
        self.client_cert = client_cert
        self.server_cert = server_cert
        self.setup_completed = True


if __name__ == "__main__":
    main = Main()
    main.run()
