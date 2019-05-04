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
        self.ocsp_responder = self.ca.get_ocsp_responder()

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
        ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.ssl_verify_cb)
        # ctx.set_verify_depth(2)
        ctx.use_privatekey(self.keys)
        ctx.use_certificate(self.cert)
        ctx.load_verify_locations(CM.get_cert_path(CONFIG["pki"]["ca-cert-name"]))
        ctx.set_ocsp_client_callback(self.ocsp_client_callback, data=self.name)

        self.context = ctx

    def connect(self, request_ocsp=True):
        if self.context is None:
            raise ConfigError("Client setup failed because context was undefined.")
        try:
            # Try to establish a TLS connection
            conn = SSL.Connection(self.context, socket(AF_INET, SOCK_STREAM))
            conn.connect((self.peer.address, self.peer.port))  # Setup connection and TLS

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
            self.accept_input()

    def disconnect(self):
        if self.verbose:
            print("Disconnecting from server...")
        try:
            self.connection.shutdown()
            self.connection.close()
            self.connection = None
        except SSL.Error as e:
            print("Could not shut down: {}".format(e))
            self.connection = None
            sys.exit(0)
        if self.verbose:
            print("Connection closed. ")

    @property
    def connected(self):
        return self.connection is not None

    def ocsp_client_callback(self, conn, ocsp, data=None):
        """
        Callback method for the OCSP certificate revocation check
        :param conn:    Connection object
        :param ocsp:    Serial number of server certificate (deviates from documented stapled OCSP assertion)
        :param data:    Data that was defined when setting the callback method, i.e. the EP name
        :return:
        """
        print("OCSP callback: {}".format(data))
        print("Server serial number: {}".format(ocsp))
        return not self.ocsp_responder.is_revoked(ocsp)  # Return True if valid, False if revoked

    def ssl_verify_cb(self, conn, cert, errno, errdepth, rcode):
        print("SSL Client verify callback")
        return errno == 0 and rcode != 0

    def accept_input(self):
        print("You can now start typing input data to send it to the server. Send an empty line or type exit to end "
              "the connection politely.")
        while True:
            line = sys.stdin.readline()
            if line == "\n" or line == "exit\n":
                self.disconnect()
                sys.exit(0)

            # TODO: Add try catch
            self.connection.send(line)
            sys.stdout.write(self.connection.recv(1024))
            sys.stdout.flush()


if __name__ == "__main__":
    print("Starting client...")
    client = Client()
    client.connect()
