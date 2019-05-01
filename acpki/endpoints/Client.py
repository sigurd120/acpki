import sys
from socket import SOCK_STREAM, socket, AF_INET, error as SocketError
from OpenSSL import SSL
from acpki.pki import CertificateManager as CM
from acpki.util.exceptions import *
from acpki.config import CONFIG
from acpki.models import EP, CertificateRequest


class Client(EP):
    def __init__(self, ca):
        super(EP, self).__init__()

        self.ca = ca

        self.ra = self.ca.get_ra()

        # Config
        self.keys = None
        self.cert = None
        self.ca_cert_name = None

        self.verbose = False
        self.peer = None
        self.context = None
        self.connection = None
        self.setup()

    def setup(self):
        # Load config
        self.name = CONFIG["endpoints"]["client-name"]
        self.address = CONFIG["endpoints"]["client-addr"]
        self.port = CONFIG["endpoints"]["client-port"]
        self.verbose = CONFIG["verbose"]

        # Create Server peer EP
        self.peer = EP(
            name=CONFIG["endpoints"]["server-name"],
            address=CONFIG["endpoints"]["server-addr"],
            port=CONFIG["endpoints"]["server-port"],
            epg=CONFIG["endpoints"]["server-epg"]
        )

        # Load or request keys and certificate
        client_pkey_name = CONFIG["pki"]["client-pkey-name"]
        client_cert_name = CONFIG["pki"]["client-cert-name"]
        self.ca_cert_name = CONFIG["pki"]["ca-cert-name"]
        if not CM.cert_file_exists(client_pkey_name) or not CM.cert_file_exists(client_cert_name):
            # Request certificate from RA
            keys = CM.create_key_pair()
            csr = CM.create_csr(keys)
            request = CertificateRequest(self, self.peer, csr)
            cert = self.ra.request_certificate(request)
            if cert is None:
                raise ConnectionError("Could not retrieve certificate needed to establish TLS connection. "
                                      "RA returned None.")

            # Save keys and certificate
            CM.save_pkey(keys, client_pkey_name)
            CM.save_cert(cert, client_cert_name)
            self.keys = keys
            self.cert = cert
        else:
            self.keys = CM.load_pkey(client_pkey_name)
            self.cert = CM.load_cert(client_cert_name)

        # Define context
        ctx = SSL.Context(SSL.TLSv1_2_METHOD)
        ctx.set_verify(SSL.VERIFY_PEER, self.ssl_verify_cb)
        ctx.use_privatekey(self.keys)
        ctx.use_certificate(self.cert)
        ctx.load_verify_locations(CM.get_cert_path(self.ca_cert_name))
        ctx.set_ocsp_client_callback(self.ocsp_client_callback, data=1)  # TODO: Add data that identifies endpoint

        self.context = ctx

    def connect(self, request_ocsp=True):
        if self.context is None:
            raise ConfigError("Client setup failed because context was undefined.")
        try:
            # Try to establish a TLS connection
            conn = SSL.Connection(self.context, socket(AF_INET, SOCK_STREAM))
            conn.connect((self.address, self.port))  # Setup connection and TLS

            if request_ocsp:
                conn.request_ocsp()
            self.connection = conn
        except SSL.Error as error:
            # TLS failed
            print("SSL error: " + str(error))
            self.connection = None
            sys.exit(1)
        except SocketError:
            # Socket failed
            print("Connection refused. Please check that the server is running and that the address and port are "
                  "correct.")
            self.connection = None
            sys.exit(1)
        else:
            print("Connected successfully to server.")
            # TODO: Validate server certificate
            self.accept_input()

    def disconnect(self, verbose=True):
        if verbose:
            print("Disconnecting from server...")
        self.connection.shutdown()
        self.connection.close()
        self.connection = None
        if verbose:
            print("Connection closed. ")

    def ssl_verify_cb(self):
        raise NotImplementedError

    @property
    def connected(self):
        return self.connection is not None

    @staticmethod
    def ocsp_client_callback(conn, ocsp, data=None):
        """
        Callback method for the OCSP certificate revocation check
        :param conn:    Connection object
        :param ocsp:    TODO: Find these from OCSP doc.
        :param data:
        :return:
        """
        print("OCSP callback")
        print(data)
        return True

    def accept_input(self):
        print("You can now start typing input data to send it to the server. Send an empty line or type exit to end "
              "the connection politely.")
        while True:
            line = sys.stdin.readline()
            if line == "" or line == "exit":
                break
            try:
                self.connection.send(line)
                sys.stdout.write(self.connection.recv(1024))
                sys.stdout.flush()
            except SSL.Error as error:
                print("Connection was closed unexpectedly")
                print("SSL ERROR:")
                print(error)
                break

        self.disconnect()


if __name__ == "__main__":
    print("Starting client...")
    client = Client()
    client.connect()
