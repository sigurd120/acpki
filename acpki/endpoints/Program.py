from acpki.endpoints import Client, Server
from acpki.pki import CA, RA
from acpki.psa import PSA
import threading, time


psa = PSA()
ca = CA(psa)
server = Server(ca)
client = Client(ca)


def run_server():
    server.connect()


def run_client():
    client.connect()


threading.Thread(target=run_server).start()
time.sleep(2)  # Wait for server to start
threading.Thread(target=run_client).start()
