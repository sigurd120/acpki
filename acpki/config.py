import os

base_dir = os.path.dirname(__file__)

CONFIG = {
    "apic": {
        "name": "sandbox-apic",
        "base-url": "sandboxapic.cisco.com",  # Should not include http://, https:// etc.
        "tn-name": "acpki_prototype",
        "ap-name": "prototype",
        "use-tls": True,
        "username": "admin",
        "password": "ciscopsdt",
        "cookie-file": "aci/private/cookie.txt",
        "token-file": "aci/private/token.txt",
        "crt-file": None,  # Setting this to None disables certificate validation, even if "use-tls" is True
        "refresh-interval": 45,
        "ws-timeout": 60
        },
    "base-dir": base_dir,
    "verbose": True,
    "pki": {
        "cert-dir": os.path.join(base_dir, "pki/certs"),
        "ca-cert-name": "root-ca.cert",
        "ca-pkey-name": "root-ca.pkey",
        "client-cert-name": "client.cert",
        "server-cert-name": "server.cert",
        "default-validity-days": 365
    }
}
