from acitoolkit import acitoolkit
import websocket, ssl, time


class Subscriber:
    ws = None

    def __init__(self, session, sub_cb):
        # Get parameters from session
        self.token = session.token
        self.sub_cb = sub_cb
        self.secure = session.secure
        self.crt_file = session.crt_file
        self.verbose = session.verbose

        # Initial setup
        self.url = self.get_ws_url(session.apic_base_url)
        self.ws = None

        self.subscribe()

    def subscribe(self):
        if self.secure and self.crt_file is not None:
            # Verify certificate
            options = {}
        else:
            # Do not verify certificate
            options = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
        print("Establishing websocket connection with the APIC...")
        ws = websocket.WebSocket(sslopt=options)
        ws.connect(self.url)

        while True:
            opcode, data = ws.recv_data()
            print("WS-{0}: {1}".format(opcode, data))
            time.sleep(1)

    def get_ws_url(self, base_url):
        if self.secure:
            prefix = "wss://"
        else:
            prefix = "ws://"
        return prefix + base_url + "/socket" + self.token
