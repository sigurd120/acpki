import time
from acpki.aci import ACISession


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self):
        # Setup
        self.session = ACISession(self.sub_cb, verbose=True)

    def sub_cb(self, data):
        print(data)


if __name__ == "__main__":
    aciadapter = ACIAdapter()
    time.sleep(10)
    aciadapter.session.get("mo/uni/tn-Heroes", subscribe=True)
