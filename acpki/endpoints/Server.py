from acpki.psa import PSA
from acpki.pki import CA, RA, CertificateManager as CM
from acpki.models import EP, CertificateRequest
from acpki.config import CONFIG
from acpki.util.exceptions import ConnectionError

import sys, socket, select, atexit
from OpenSSL import SSL


class Server(EP):
    """
    This simple Server class is able to establish a TLS 1.2 connection with ONE client at a time using the certificates
    issued by the CA and the PSA. For a connection to be approved, the corresponding EPGs must be added to the connected
    Cisco APIC (e.g. Cisco APIC Sandbox). The particular EPs DO NOT have to be added to Cisco ACI, as these only exist
    virtually and there is no validation of EPG relations in this prototype. The server class can be run individually,
    and must be started before the Client class.
    """
    def __init__(self, ca):
        super(EP, self).__init__()  # Initiate without values, override below

        self.ca = ca

        self.ra = self.ca.get_ra()
        self.peer = None
        self.verbose = True
        self.cert = None
        self.keys = None

        self.context = None     # Will be specified during setup()
        self.connection = None  # SSL.Connection object, established on connect()
        self.rlist = {}         # Reader list (clients)
        self.wlist = {}         # Writer list (clients)

        # Setup
        atexit.register(self.disconnect)

    def setup(self, peer=None, epg=None):
        # Load config
        self.name = CONFIG["endpoints"]["server-name"]
        self.address = CONFIG["endpoints"]["server-addr"]
        self.port = CONFIG["endpoints"]["server-port"]
        self.verbose = CONFIG["verbose"]

        self.epg = epg
        self.peer = peer

        # Create Client peer
        self.peer = EP(
            name=CONFIG["endpoints"]["client-name"],
            address=CONFIG["endpoints"]["client-addr"],
            port=CONFIG["endpoints"]["client-port"],
            epg=CONFIG["endpoints"]["client-epg"]
        )

        # Load key material to create or request connection-specific certificate
        server_pkey_name = CONFIG["pki"]["server-pkey-name"]
        server_cert_name = CONFIG["pki"]["server-cert-name"]
        if not CM.cert_file_exists(server_pkey_name) or not CM.cert_file_exists(server_cert_name):
            # Request certificate from RA
            keys = CM.create_key_pair()
            csr = CM.create_csr(keys)
            request = CertificateRequest(self, self.peer, csr)
            cert = self.ra.request_certificate(request)
            if cert is None:  # TODO: Validate own certificate
                raise ConnectionError("Could not retrieve certificate needed to establish TLS connection.")

            # Save keys and certificate
            CM.save_pkey(keys, server_pkey_name)
            CM.save_cert(cert, server_cert_name)
            self.cert = cert
            self.keys = keys
        else:
            self.keys = CM.load_pkey(server_pkey_name)
            self.cert = CM.load_cert(server_cert_name)

        # Create context
        self.context = SSL.Context(SSL.TLSv1_2_METHOD)
        #self.context.set_options(SSL.OP_NO_SSLv2)
        #self.context.set_options(SSL.OP_NO_SSLv3)
        self.context.set_options(SSL.OP_NO_TLSv1_2)
        self.context.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.ssl_verify_cb)
        self.context.set_ocsp_server_callback(self.ocsp_server_cb, data=self.name)

        # TODO: Add try catch here and verify context
        self.context.use_privatekey(self.keys)
        self.context.use_certificate(self.cert)
        self.context.load_verify_locations(CM.get_cert_path(CONFIG["pki"]["ca-cert-name"]))

    def get_cert(self):
        return self.cert

    def connect(self):
        if self.context is None:
            raise ConnectionError("Cannot connect before context has been created.")

        # TODO: Add try catch

        # Create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection = SSL.Connection(self.context, sock)

        try:
            self.connection.bind((self.address, self.port))
            self.connection.set_accept_state()
            self.connection.listen(3)
            self.connection.setblocking(0)
        except Exception as e:
            print("Server could not connect")
            raise e

        self.listen()

    def disconnect(self):
        print("Server is shutting down...")
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            print("Connection closed")

    def drop_client(self, cli, errors=None):
        if errors:
            print("Connection with client {0} was closed unexpectedly.".format(self.rlist[cli]))
        else:
            print("Client {0} closed the connection.".format(self.rlist[cli]))
        del self.rlist[cli]
        if cli in self.wlist:
            del self.wlist[cli]
        if errors is None:
            cli.shutdown()
        cli.close()

    def listen(self):
        if self.connection is None:
            raise ConnectionError("Connection attribute was undefined. Cannot listen until you have connected!")
        else:
            print("Server is listening for clients. Connect at {0}:{1}".format(self.address, self.port))

        # Listen to new connections and incoming data
        while True:
            try:
                rlist, wlist, xlist = select.select([self.connection] + self.rlist.keys(), self.wlist.keys(), [])
            except Exception as e:
                print("ERROR: Connection failed, shutting down... {}".format(e))
                break

            # Readers
            for cli in rlist:
                if cli == self.connection:
                    # New client
                    cli, addr = self.connection.accept()
                    print("Established connection with client at {0}:{1}".format(addr[0], addr[1]))
                    self.rlist[cli] = addr
                else:
                    # Incoming data
                    try:
                        data = cli.recv(2048)
                    except SSL.ZeroReturnError:
                        self.drop_client(cli)
                    except SSL.Error, errors:
                        self.drop_client(cli, errors)
                    else:
                        if not self.wlist.has_key(cli):
                            self.wlist[cli] = ""
                        self.wlist[cli] = self.wlist[cli] + data

            # Writers
            for cli in wlist:
                try:
                    data = cli.send(self.wlist[cli])
                except SSL.ZeroReturnError:
                    self.drop_client(cli)
                except (SSL.WantReadError, SSL.WantWriteError, SSL.WantX509LookupError):
                    pass
                except SSL.Error, errors:
                    self.drop_client(cli, errors)
                else:
                    self.wlist[cli] = self.wlist[cli][data:]
                    if self.wlist[cli] == "":
                        del self.wlist[cli]

        # While loop ended, close connections
        for cli in self.rlist.keys():
            cli.close()
        self.connection.close()

    def ocsp_server_cb(self, conn, data=None):
        """
        The OCSP callback method is responsible for ensuring that the certificate is still valid. The request should be

        :param conn:
        :param data:
        :return:
        """
        print("OCSP callback: {}".format(data))
        return str(self.cert.get_serial_number()).encode()

    def ssl_verify_cb(self, conn, cert, errno, errdepth, rcode):
        print("SSL Server verify callback")
        return errno == 0 and rcode != 0


if __name__ == "__main__":
    psa = PSA()
    ca = CA(psa)
    server = Server(ca)
    print("Server was initiated")
