from acitoolkit import acitoolkit
import websocket, ssl, time, threading
from acpki.aci import Subscription


class Subscriber:
    ws = None

    def __init__(self, aci_session, sub_cb):
        # Get parameters from session
        self.token = aci_session.token
        self.sub_cb = sub_cb
        self.secure = aci_session.secure
        self.crt_file = aci_session.crt_file
        self.verbose = aci_session.verbose

        # Initial setup
        self.url = self.get_ws_url(aci_session.apic_base_url)
        self.ws = None
        self.thread = None
        self.connected = False
        self.subscriptions = []

        self.connect()

    def connect(self):
        # Security options
        if self.secure and self.crt_file is not None:
            # Verify certificate
            options = {}
        else:
            # Do not verify certificate
            options = {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}

        # Create websocket
        print("Establishing websocket connection with the APIC...")
        self.ws = websocket.WebSocket(sslopt=options)

        # Connect
        # TODO: Find out what errors this can cause and catch them.
        self.ws.connect(self.url)
        print("Websocket connected successfully.")
        self.connected = True

        # Create WS work thread
        self.thread = threading.Thread(target=self.listen)
        self.thread.start()

        return

    def listen(self):
        """
        Does NOT need to be called to listen. This is called automatically by the thread created in the connect()
        method.
        :return:    Any data received from the work thread, None otherwise
        """
        print("Thread opened, listening for updates from the APIC...")
        while True:
            opcode, data = self.ws.recv_data()
            print("WS-{0}: {1}".format(opcode, data))
            time.sleep(1)

    def subscribe(self, id, method):
        subscription = Subscription(id, method)
        self.subscriptions.append(subscription)

    def unsubscribe(self, id):
        raise NotImplementedError()

    def get_ws_url(self, base_url):
        if self.secure:
            prefix = "wss://"
        else:
            prefix = "ws://"
        return prefix + base_url + "/socket" + self.token
