import requests, pickle, sys, os, json, thread, time
import urllib3
import websocket
from acpki.util.custom_exceptions import SessionError, SubscriptionError
from acpki.aci import Subscriber, Subscription


class ACISession:
    """
    This class is responsible for the sessions with Cisco ACI, which are responsible for all communication and
    subscriptions with the APIC.
    """
    def __init__(self, sub_cb=None, verbose=False):
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
        self.sub_cb = sub_cb

        self.username = "admin"
        self.password = "ciscopsdt"
        self.cookie_file = "private/cookie.txt"
        self.token_file = "private/token.txt"

        # Set initial values
        self.crt_file = None
        self.token = None
        self.session = None
        self.subscriber = None

        # Setup and connect
        self.setup()
        self.connect()

        # Initiate Subscriber object
        if sub_cb is not None:
            self.subscriber = Subscriber(self, sub_cb)

    def setup(self):
        # Disable certificate verification -- this is not provided by Cisco ACI
        # TODO: Look into whether certificate can be validated against Cisco's root certificate
        if self.crt_file is None:
            print("APIC Certificate verification is not disabled. For improved security, please provide a certificate "
                  "file in the configuration. ")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_method_path(self, method, file_format="json"):
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
        path = self.get_method_path("aaaLogin")
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

    def get(self, method, file_format=None, silent=False, subscribe=False, **kwargs):
        """
        Get method that adds the necessary parameters and URL.
        :param method:          ACI method name, i.e. what is following apic-url/api/, excluding .json and .xml
        :param file_format:     Format of returned data, either "json", "xml" or None (default)
        :param silent:          Packet will be sent silently, overriding self.verbose
        :param subscribe:       Subscribe to updates in the information queried, requires an active WebSocket
        :return:                A requests response object
        """
        # Get file format
        if file_format is None:
            path = self.get_method_path(method)
        else:
            path = self.get_method_path(method, file_format)

        # Get keyword arguments as GET parameters
        if subscribe:
            kwargs["subscription"] = "yes"

        if len(kwargs.keys()) > 0:
            path += ACISession.dict_to_get(kwargs)

        # Check current session and subscription
        if self.session is None:
            raise SessionError("Cannot send GET request without a session!")

        if subscribe and self.subscriber is None:
            raise SubscriptionError("Could not subscribe as no Subscriber was found for session")
        elif subscribe and not self.subscriber.connected:
            raise SubscriptionError("Could not subscribe as Subscriber was disconnected.")

        # Analyse and print response (if verbose mode)
        resp = self.session.get(path, verify=False)
        if self.verbose and not silent:
            print("GET {0}".format(path))
            print("Reponse: {0} {1}".format(resp.status_code, resp.reason))

        # Create subscription
        if subscribe and resp.ok:
            if self.verbose:
                print("Creating new subscription")
            json_resp = json.loads(resp.content)
            self.subscriber.subscribe(json_resp["subscriptionId"], method)
            print(self.subscriber.subscriptions)

        return resp

    @staticmethod
    def dict_to_get(dict):
        ret = ""
        for i, key in enumerate(dict.keys()):
            ret += "?" if i == 0 else "&"
            ret += key + "=" + dict[key]
        return ret

    @staticmethod
    def extract_token(response):
        content = json.loads(response.content)
        return content["imdata"][0]["aaaLogin"]["attributes"]["token"]