from acitoolkit import acitoolkit
import websocket, ssl, time, thread, threading
from acpki.aci import Subscription
from work_threads import WSThread, RefreshThread
from acpki.util.exceptions import SubscriptionError


class Subscriber:
    def __init__(self, aci_session):
        # Get parameters from session
        self.token = aci_session.token
        # self.cookies = aci_session.get_cookies()
        self.secure = aci_session.secure
        self.crt_file = aci_session.crt_file
        self.verbose = aci_session.verbose

        # Initial setup
        self.url = self.get_ws_url(aci_session.apic_base_url)
        self.session = aci_session
        self.ws = None
        self.ws_thread = None
        self.refresh_thread = None
        self.refresh_interval = 45
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
        self.ws.settimeout(60)
        self.ws.connect(self.url)
        print("Websocket connected successfully.")
        self.connected = True

        # Create WS work threads
        self.ws_thread = WSThread(self.ws, self.sub_cb)
        self.refresh_thread = RefreshThread(self.ws, self.refresh_subscriptions, self.refresh_interval)

        print("WS opened: {}".format(self.url))

        return

    def sub_cb(self, opcode, data):
        """
        This method maps incoming subscription data to its respective callback method.
        :param opcode:      The WS identifier for the incoming data
        :param data:        Subscription data
        :return:
        """
        print("Sub CB {0}: {1}".format(opcode, data))

    def disconnect(self):
        if self.verbose:
            print("Closing websocket...")

        if not self.connected:
            print("You are not connected.")
            return True

        # Exit threads
        self.ws_thread.stop()
        self.ws_thread = None
        self.refresh_thread.stop()
        self.refresh_thread = None

        # Clear subscriptions
        self.subscriptions = []

        # Clear websocket
        self.ws.close()
        self.connected = False
        return True

    def reconnect(self):
        self.disconnect()
        self.connect()

    def refresh_subscriptions(self):
        for subscription in self.subscriptions:
            if self.verbose:
                print("Refreshing subscription {}".format(subscription.sid))
            if not isinstance(subscription, Subscription):
                if self.verbose:
                    raise SystemError("Encountered object inside Subscriber.subscriptions that was not of type "
                                      "Subscription. I do not know what to do with that. ")
            resp = self.session.get("subscriptionRefresh", params={"id": subscription.sid})
            if resp.ok:
                print("Subscription {0} was successfully refreshed.".format(subscription.sid))
            else:
                print("Could not refresh session. Status: {0} {1}".format(resp.status_code, resp.reason))

    def subscribe(self, sid, method, callback=None):
        """
        This method is called when a new subscription IS generated. To create a new subscription, use the
        ACISession.get() method with subscription=True as an optional parameter.
        :param sid:         Subscription ID of the generated subscription
        :param method:      Method for which the subscription is created, i.e. what is following apic/api/...
        :param callback:    Callback method to which the result will be passed for given subscription
        :return:
        """
        subscription = Subscription(sid, method, callback)
        self.subscriptions.append(subscription)

    def unsubscribe(self, id):
        raise NotImplementedError()

    def get_ws_url(self, base_url):
        if self.secure:
            prefix = "wss://"
        else:
            prefix = "ws://"
        return prefix + base_url + "/socket" + self.token
