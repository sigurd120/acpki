from acpki.endpoints import Client, Server2
from acpki.pki import CA, RA
from acpki.psa import PSA


psa = PSA()
ca = CA(psa)
server = Server2(ca)
client = Client(ca)

# TODO: Move to threads so they can work simultaneously
server.connect()
client.connect()