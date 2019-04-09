import sys, os, time
from acpki.aci import ACISession
from acpki.config import CONFIG
from acpki.util.exceptions import RequestError


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self):
        # Setup
        self.tenant_name = CONFIG["apic"]["tn-name"]
        self.ap_name = CONFIG["apic"]["ap-name"]
        self.session = ACISession(self.subscription_callback, verbose=True)

    def connect(self):
        # Connect to APIC
        self.session.connect()
        time.sleep(3)
        # aciadapter.session.get("mo/uni/tn-acpki_prototype", subscribe=True)

        self.get_epgs()

    def disconnect(self):
        self.session.disconnect()

    def get_epgs(self):
        params = {
            "query-target": "children",
            "target-subtree-class": "fvAEPg",
            "query-target-filter": "eq(fvAEPg.isAttrBasedEPg,\"false\")",
            "order-by": "fvAEPg.name|asc"
        }

        url = "node/mo/uni/tn-{0}/ap-{1}".format(self.tenant_name, self.ap_name)
        resp = self.session.get(url, "json", subscribe=True)
        if resp.ok:
            return resp.content
        else:
            raise RequestError("Could not get EPGs from the APIC. Please check the request URL, GET parameters, "
                               "configuration and that the APIC is available before trying again.")

    @staticmethod
    def subscription_callback(opcode, data):
        print("WebSocket {0}: {1}".format(opcode, data))


if __name__ == "__main__":
    aciadapter = ACIAdapter()
    try:
        aciadapter.connect()
        time.sleep(3)
    except KeyboardInterrupt:
        print("Keyboard interrupt. Shutting down...")
        aciadapter.disconnect()
