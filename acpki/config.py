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
        "crt-file": None,   # Setting this to None disables certificate validation, even if "use-tls" is True. This is
                            # required when using the APIC Sandbox from Cisco.
        "refresh-interval": 45,
        "ws-timeout": 60,
        },
    "base-dir": base_dir,
    "verbose": True,
    "pki": {
        "cert-dir": os.path.join(base_dir, "pki/certs"),
        "ca-cert-name": "root-ca.cert",
        "ca-pkey-name": "root-ca.pkey",
        "ra-cert-name": "ra.cert",
        "ra-pkey-name": "ra.pkey",
        "client-cert-name": "client.cert",
        "client-pkey-name": "client.pkey",
        "server-cert-name": "server.cert",
        "server-pkey-name": "server.pkey",
        "default-validity-days": 365,
    },
    "endpoints": {
        "client-name": "client-endpoint",
        "client-addr": "127.0.0.1",
        "client-port": 13150,
        "client-epg": "epg-cli",
        "server-name": "server-endpoint",
        "server-addr": "127.0.0.1",
        "server-port": 13151,
        "server-epg": "epg-serv",
    },
    "psa": {
        "ous-file": os.path.join(base_dir, "psa/ous.txt"),
    }
}
