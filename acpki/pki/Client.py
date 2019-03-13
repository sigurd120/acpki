import sys
from socket import SOCK_STREAM, socket, AF_INET
from OpenSSL import SSL
from acpki.pki import CommAgent, CertificateManager
from acpki.util.custom_exceptions import *


class Client(CommAgent):
    def __init__(self):
        # Config
        self.private_key = "client.pkey"
        self.certificate = "client.cert"
        self.ca_certificate = "ca.cert"

        self.context = self.get_context()
        self.connection = None

        super(Client, self).__init__()

    def connect(self):
        if self.context is None:
            raise ConfigError("Client setup failed because context was undefined.")
        try:
            self.connection = SSL.Connection(self.context, socket(AF_INET, SOCK_STREAM))
            self.connection.connect((self.serv_addr, self.serv_port))  # Setup connection and TLS
        except SSL.Error as error:
            print("SSL error: " + error)
            sys.exit(1)
        else:
            print("Connected successfully to server.")
            self.accept_input()

    def disconnect(self, verbose=True):
        if verbose:
            print("Disconnecting from server...")
        self.connection.shutdown()
        self.connection.close()
        self.connection = None
        if verbose:
            print("Connection closed. ")

    @property
    def connected(self):
        return self.connection is not None

    def get_context(self):
        context = SSL.Context(SSL.TLSv1_2_METHOD)
        context.set_verify(SSL.VERIFY_PEER, self.ssl_verify_cb)
        context.use_privatekey_file(CertificateManager.get_cert_path(self.private_key))
        context.use_certificate_file(CertificateManager.get_cert_path(self.certificate))
        context.load_verify_locations(CertificateManager.get_cert_path(self.ca_certificate))
        return context

    def accept_input(self):
        print("You can now start typing input data to send it to the server. Send an empty line or type exit to stop.")
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
