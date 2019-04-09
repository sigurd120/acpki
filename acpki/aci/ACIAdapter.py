import sys, os, time
from acpki.aci import ACISession


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self):
        # Setup
        self.session = ACISession(self.subscription_callback, verbose=True)

    def connect(self):
        # Connect to APIC
        self.session.connect()
        time.sleep(3)
        aciadapter.session.get("mo/uni/tn-acpki_prototype", subscribe=True)

    def disconnect(self):
        self.session.disconnect()

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
