from acitoolkit import acitoolkit
import websocket, ssl, time, thread, threading
from acpki.aci import Subscription
from ws_thread import WSThread


class Subscriber:
    ws = None

    def __init__(self, aci_session, sub_cb):
        # Get parameters from session
        self.token = aci_session.token
        self.cookies = aci_session.get_cookies()
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

        # Connect
        # TODO: Find out what errors this can cause and catch them.

        self.ws = websocket.WebSocket(sslopt=options)
        self.ws.connect(self.url)
        print("Websocket connected successfully.")
        self.connected = True
        """
        self.ws = websocket.WebSocketApp(
            self.url,
            on_data=self.on_data,
            on_error=self.on_error,
            on_close=self.on_close,
            cookie=self.cookies
        )
        """

        # Create WS work thread
        self.thread = WSThread(self.ws)

        print("WS opened: {}".format(self.url))

        return

    def disconnect(self):
        if self.verbose:
            print("Closing websocket...")
        self.ws.close()
        self.thread.exit_thread()

    def reconnect(self):
        self.disconnect()
        self.connect()

    def beat(self):
        """
        DO NOT call this method directly. It should only be called by the thread established in the connect() method.
        Contains all actions that need to be performed at a regular interval by the Subscriber class, including
        listening for new data and refresh the session when needed.
        :return:    Any data received from the work thread, None otherwise
        """
        print("Thread opened, listening for updates from the APIC...")
        while True:
            opcode, data = self.ws.recv_data()
            print("WS-{0}: {1}".format(opcode, data))
            time.sleep(1)

    def refresh_subscriptions(self):
        raise NotImplementedError()

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
