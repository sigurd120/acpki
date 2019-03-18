import sys, socket, select, atexit
from OpenSSL import SSL
from acpki.util.custom_exceptions import *
from acpki.pki import CommAgent, CertificateManager


class Server(CommAgent):
    """
    This simple Server class accepts Client connections and echoes back messages that it receives.
    """
    def __init__(self):
        self.private_key = "server.pkey"
        self.certificate = "server.cert"
        self.ca_certificate = "ca.cert"

        self.context = self.get_context()
        self.connection = None
        self.clients = {}
        self.writers = {}  # TODO: Required? What is this?

        atexit.register(self.shutdown)
        super(Server, self).__init__()

    def server_setup(self):
        if self.context is None:
            raise ConfigError("Server setup failed because context was undefined.")
        try:
            self.connection = SSL.Connection(self.context, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            self.connection.bind((self.serv_addr, self.serv_port))
            self.connection.set_accept_state()
            self.connection.listen(3)
            self.connection.setblocking(0)
        except SSL.Error:
            print("Could not set up TLS connection on " + self.serv_addr + ":" + self.serv_port)
            sys.exit(1)
        else:
            print("Server was successfully set up.")
            self.listen()

    def shutdown(self):
        print("Server is shutting down...")
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            print("Connection closed")

    def get_context(self):
        context = SSL.Context(SSL.TLSv1_2_METHOD)
        context.set_options(SSL.OP_NO_TLSv1_2)
        context.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.ssl_verify_cb)
        context.set_ocsp_server_callback(self.ocsp_server_callback)
        try:
            context.use_privatekey_file(CertificateManager.get_cert_path(self.private_key))
            context.use_certificate_file(CertificateManager.get_cert_path(self.certificate))
            context.load_verify_locations(CertificateManager.get_cert_path(self.ca_certificate))
        except SSL.Error:
            print("Error: Could not load key and certificate files. Please make sure that you have run the setup.py"
                  "script before starting Server.py.")
        return context

    @staticmethod
    def ocsp_server_callback(conn, data=None):
        print("OCSP server callback")
        print(data)
        return True

    def drop_client(self, cli, errors=None):
        """
        Drop a server client, intentionally or unexpectedly.
        :param cli:         The client to drop
        :param errors:      Errors associated with the drop (optional)
        """
        if errors:
            print("Connection with client {0} was closed unexpectedly.".format(self.clients[cli]))
            # print(errors)
        else:
            print("Client {0} closed the connection.".format(self.clients[cli]))
        del self.clients[cli]
        if self.writers.has_key(cli):
            del self.writers[cli]
        if errors is None:
            cli.shutdown()
        cli.close()

    def listen(self):
        if self.connection is None:
            raise ConfigError("Server has not been set up correctly.")
        else:
            print("Server is listening for clients...")

        while True:
            try:
                r, w, _ = select.select([self.connection]+self.clients.keys(), self.writers.keys(), [])
            except:
                break

            for cli in r:
                if cli == self.connection:
                    cli, addr = self.connection.accept()
                    print("Connection established with {0}:{1}".format(addr[0], addr[1]))
                    self.clients[cli] = addr
                else:
                    try:
                        ret = cli.recv(1024)
                    except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
                        pass
                    except SSL.ZeroReturnError:
                        self.drop_client(cli)
                    except SSL.Error, errors:
                        self.drop_client(cli, errors)
                    else:
                        if not self.writers.has_key(cli):
                            self.writers[cli] = ""
                        self.writers[cli] = self.writers[cli] + ret

            for cli in w:
                try:
                    ret = cli.send(self.writers[cli])
                except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
                    pass
                except SSL.ZeroReturnError:
                    self.drop_client(cli)
                except SSL.Error, errors:
                    self.drop_client(cli, errors)
                else:
                    self.writers[cli] = self.writers[cli][ret:]
                    if self.writers[cli] == "":
                        del self.writers[cli]

        # Close active connections
        for cli in self.clients.keys():
            cli.close()
        self.connection.close()


if __name__ == "__main__":
    print("Starting server...")
    server = Server()
    server.server_setup()
    server.listen()
