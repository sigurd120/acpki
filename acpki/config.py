import os

CONFIG = {
    "apic": {
        "name": "sandbox-apic",
        "base-url": "sandboxapic.cisco.com",  # Should not include http://, https:// etc.
        "tn-name": "apic_prototype",
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
    "base-dir": os.path.dirname(__file__),
    "verbose": True
}
