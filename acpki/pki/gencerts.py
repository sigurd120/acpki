from OpenSSL import crypto
from acpki.pki import CertificateManager
import os

"""
This file creates the basic certificates needed to use the AC-PKI system. The program should be called from the general
config script. If files already exist, this script WILL NOT replace them by default. Note that certificate files ARE NOT
shared via Git and will therefore need to be created on each individual system. 
"""

print("Setting up certificates...")

# Create certs directory if it does not already exist
if not os.path.exists(CertificateManager.get_cert_path()):
    os.makedirs(CertificateManager.get_cert_path())
    print("Created certs directory")

# Create CA certificate
if CertificateManager.cert_file_exists("ca.cert") and CertificateManager.cert_file_exists("ca.pkey"):
    # Load existing
    print("Loading existing CA certificate from file")
    ca_cert = CertificateManager.load_cert("ca.cert")
    ca_key_pair = CertificateManager.load_pkey("ca.pkey")
else:
    # Generate new
    print("Generating CA certificate")
    ca_key_pair = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
    csr = CertificateManager.create_csr(ca_key_pair, C="NO", ST="Oslo", O="Corp", OU="Blab")
    ca_cert = CertificateManager.create_self_signed_cert(csr, ca_key_pair, 0)
    CertificateManager.save_pkey(ca_key_pair, "ca.pkey")
    CertificateManager.save_cert(ca_cert, "ca.cert")

# Create client certificate
if CertificateManager.cert_file_exists("client.cert") and CertificateManager.cert_file_exists("client.pkey"):
    # Load existing
    print("Loading existing client certificate from file")
    client_cert = CertificateManager.load_cert("client.cert")
else:
    # Generate new
    print("Generating client certificate")
    client_key_pair = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
    csr = CertificateManager.create_csr(client_key_pair, C="NO", ST="Oslo", O="Corp", OU="abc123")
    client_cert = CertificateManager.create_cert(csr, 1, ca_cert.get_subject(), ca_key_pair)
    CertificateManager.save_cert(client_cert, "client.cert")
    CertificateManager.save_pkey(client_key_pair, "client.pkey")

# Create server certificate
if CertificateManager.cert_file_exists("server.cert") and CertificateManager.cert_file_exists("server.pkey"):
    # Load existing
    print("Loading existing server certificate from file")
    server_cert = CertificateManager.load_cert("server.cert")
else:
    # Generate new
    print("Generating server certificate")
    server_key_pair = CertificateManager.create_key_pair(crypto.TYPE_RSA, 2048)
    csr = CertificateManager.create_csr(server_key_pair, C="NO", ST="Oslo", O="Corp", OU="abc321")
    server_cert = CertificateManager.create_cert(csr, 2, ca_cert.get_subject(), ca_key_pair)
    CertificateManager.save_cert(server_cert, "server.cert")
    CertificateManager.save_pkey(server_key_pair, "server.pkey")
