import requests, pickle, sys, os, json, thread, time
import urllib3
import websocket
from acpki.util.exceptions import SessionError, SubscriptionError
from acpki.aci import Subscriber, Subscription
from acpki.config import CONFIG


class ACISession:
    """
    This class is responsible for the sessions with Cisco ACI, which are responsible for all communication and
    subscriptions with the APIC.
    """
    def __init__(self, verbose=False):
        """
        Constructor for the ACISession class.
        :param sub_cb:      Callback method for subscriptions - if not provided subscriptions are disabled for session
        :param verbose:     Verbose mode (provides more output)
        """
        # Configuration
        self.secure = True
        self.connected = False
        self.verbose = verbose
        self.apic_base_url = "sandboxapicdc.cisco.com"
        self.apic_web_url = self.get_web_url(self.apic_base_url)

        # Credentials and authentication
        self.username = "admin"
        self.password = "ciscopsdt"
        self.cookie_file = os.path.join(CONFIG["base-dir"], CONFIG["apic"]["cookie-file"])
        self.token_file = os.path.join(CONFIG["base-dir"], CONFIG["apic"]["token-file"])

        # Set initial values
        self.crt_file = None
        self.verify = self.crt_file is not None  # TODO: Find out how this works...
        self.token = None
        self.session = None
        self.subscriber = None
        self.cb_methods = {}

        # Setup and connect
        self.setup()

    def setup(self):
        # Disable certificate verification -- this is not provided by Cisco ACI
        # TODO: Look into whether certificate can be validated against Cisco's root certificate
        if self.crt_file is None:
            print("APIC Certificate verification is not disabled. For improved security, please provide a certificate "
                  "file in the configuration. ")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_method_url(self, method, file_format="json"):
        return self.apic_web_url + "/api/" + method + "." + file_format

    def get_web_url(self, base_url):
        if self.secure:
            prefix = "https://"
        else:
            prefix = "http://"
        return prefix + base_url

    def connect(self, force_auth=False):
        """
        Standard method for connecting with the APIC. Attempts to resume session based on the stored session cookie. If
        the cookie does not exist or has expired it authenticates.
        :param sub_cb:      Callback method for any subscription created in this session (Default: None)
        :param force_auth:  Will not attempt to resume session, and authenticate even with a valid session cookie
        :return:
        """
        if not force_auth and self.resume_session():
            # Resumed session from cookie
            print("Successfully resumed saved session.")
        else:
            # Force authentication or resume failed
            print("Session undefined or expired. Authenticating...")
            res = self.authenticate()
            print("Result: {0} {1}".format(res.status_code, res.reason))
            if not res.ok:
                print("Could not log in... Please check the above status code.")
                sys.exit(1)

        # Create subscriber
        self.subscriber = Subscriber(self, sub_cb=self.callback)

    def callback(self, opcode, data):
        """
        When receiving WebSocket data, this method maps the subscription to its assigned callback method and forwards
        the data to that method. If the method is not found it executes default code.
        :param opcode:      Op code, i.e. reference to the related WebSocket
        :param data:        Subscription data, JSON or XML data that describes the changes
        :return:
        """
        content = json.loads(data)
        sub_id = content["subscriptionId"][0]  # TODO: Find out why multiple sub ids can be returned
        if sub_id in self.cb_methods.keys():
            # Callback method found
            cb = self.cb_methods[sub_id]
            print("Found matching callback method. Forwarding data to that...")
            cb(opcode, data)
        else:
            # Callback method not found, default
            print("No matching CB method. Using default:")
            print("Callback WS-{0}: {1}".format(opcode, data))

    def disconnect(self):
        if self.verbose:
            print("Disconnecting...")
        self.subscriber.disconnect()
        self.connected = False

    def resume_session(self):
        """
        If AC-PKI has recently been logged in, this method will resume the session by loading the current cookies from
        file. Otherwise, it will authenticate and create a new session.
        :return:    True if successful, False otherwise
        """
        # Load cookies
        if self.cookie_file and os.path.exists(self.cookie_file):
            # Load cookies from file
            session = requests.session()
            with open(self.cookie_file, "rb") as f:
                session.cookies.update(pickle.load(f))

            self.session = session
        else:
            # Abort session resumption
            return False

        # Load token
        if self.token_file and os.path.exists(self.token_file):
            with open(self.token_file, "r") as f:
                self.token = f.readline()
        else:
            # Abort session resumption
            return False

        return self.check_connection()

    def authenticate(self):
        """
        Authenticate with the APIC. This method should not be called directly, use connect() instead as it allows for
        optional session resumption.
        :return:
        """
        # Prepare and send auth request
        self.session = requests.Session()
        login = {"aaaUser":{"attributes": {"name": self.username, "pwd": self.password}}}
        path = self.get_method_url("aaaLogin")
        resp = self.session.post(path, json=login, verify=False)

        # Verify response from APIC
        if self.verbose and resp.ok:
            print("Successfully logged in.")
        else:
            print("Error: {0} {1}".format(resp.status_code, resp.reason))
            print("Authentication with the Cisco APIC failed. Terminating...")
            sys.exit(1)

        # Save cookie
        if self.cookie_file:
            try:
                with open(self.cookie_file, "wb") as f:
                    pickle.dump(self.session.cookies, f)
            except IOError:
                print("Could not save session. Continuing without persistency...")

        # Save token
        self.token = self.extract_token(resp)
        if self.token_file:
            try:
                with open(self.token_file, "w") as f:
                    f.write(self.token)
                    print("Token saved in file.")
            except IOError:
                raise SystemError("Could not save token to file.")

        return resp

    def check_connection(self):
        """
        Checks whether the class is successfully connected with the APIC and sets the self.connected parameter
        accordingly.
        :return:    Current connection status (True or False)
        """
        resp = self.get("mo/uni/tn-common", silent=True)  # Get common tenant (which should always exist in Cisco ACI)
        self.connected = resp.ok is True
        if self.verbose:
            print("Connection status: {0} {1}".format(resp.status_code, resp.reason))
        return self.connected

    def get_cookies(self):
        return self.session.cookies

    def get(self, method, file_format=None, silent=False, subscribe=False, sub_cb=None, params={}):
        """
        Get method that adds the necessary parameters and URL.
        :param method:          ACI method name, i.e. what is following apic-url/api/, excluding .json and .xml
        :param file_format:     Format of returned data, either "json", "xml" or None (default)
        :param silent:          Packet will be sent silently, overriding self.verbose
        :param subscribe:       Subscribe to updates in the information queried, requires an active WebSocket
        :param sub_cb:          Callback method to which subscription data will be sent
        :param params:          Dictionary of GET parameters to add to URL, excluding "subscription" which is enabled by
                                setting the "subscribe" attribute (above)
        :return:                A requests response object
        """
        # Get file format
        if file_format is None:
            path = self.get_method_url(method)
        else:
            path = self.get_method_url(method, file_format)

        # Add GET parameters to path
        if subscribe:
            params["subscription"] = "yes"

        for i, key in enumerate(params.keys()):
            path += "?" if i == 0 else "&"
            path += key + "=" + params[key]

        # Check current session and subscription
        if self.session is None:
            raise SessionError("Cannot send GET request without a session!")

        if subscribe and self.subscriber is None:
            raise SubscriptionError("Could not subscribe as no Subscriber was found for session")
        elif subscribe and not self.subscriber.connected:
            raise SubscriptionError("Could not subscribe as Subscriber was disconnected.")

        # Analyse and print response (if verbose mode)
        resp = self.session.get(path, verify=self.verify)
        if self.verbose and not silent:
            print("GET {0}".format(path))
            print("Reponse: {0} {1}".format(resp.status_code, resp.reason))

        # Create subscription
        if subscribe and resp.ok:
            if self.verbose:
                print("Creating new subscription")
            json_resp = json.loads(resp.content)

            # Subscribe and save reference to subscription callback
            sub = self.subscriber.subscribe(json_resp["subscriptionId"], method, callback=sub_cb)
            self.cb_methods[sub.sub_id] = sub.callback

        return resp

    def post(self, method, jsn):
        url = self.get_method_url(method, "json")  # JSON is only supported file_format for POST requests

        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache"
        }

        response = self.session.request("POST", url, data=jsn, headers=headers, verify=self.verify)
        return response


    def unsubscribe(self, sub_id):
        raise NotImplementedError("Method not implemented. Let the subscription expire for now.")  # TODO: Implement

    @staticmethod
    def extract_token(response):
        content = json.loads(response.content)
        return content["imdata"][0]["aaaLogin"]["attributes"]["token"]
