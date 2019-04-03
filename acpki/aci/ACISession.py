import requests, pickle, sys, os, json, thread, time
import urllib3
import websocket
from acpki.util.custom_exceptions import SessionError
from acpki.aci import Subscriber


class ACISession:
    """
    This class is responsible for the sessions with Cisco ACI, which are responsible for all communication and
    subscriptions with the APIC.
    """
    def __init__(self, sub_cb=None, verbose=False):
        # Configuration
        self.apic_base_url = "sandboxapicdc.cisco.com"
        self.apic_web_url = "https://" + self.apic_base_url
        self.username = "admin"
        self.password = "ciscopsdt"
        self.cookie_file = "private/cookie.txt"
        self.token_file = "private/token.txt"
        self.crt_file = None
        self.token = None
        self.session = None
        self.subscription = None
        self.connected = False
        self.verbose = verbose
        self.secure = True

        # Setup and connect
        self.setup()
        self.connect()

        if sub_cb is not None:
            # Subscribe
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

    def connect(self, subscribe=False, force_auth=False):
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
            elif subscribe:
                self.subscription = Subscriber(self.get_ws_url(), self.token)

    def resume_session(self):
        """
        If AC-PKI has recently been logged in, this method will resume the session by loading the current cookies from
        file. Otherwise, it will authenticate and create a new session.
        :return:    True if successful, False otherwise
        """
        if self.cookie_file and os.path.exists(self.cookie_file):
            # Load cookies from file
            session = requests.session()
            with open(self.cookie_file, "rb") as f:
                session.cookies.update(pickle.load(f))

            self.session = session
            return self.check_connection()

    def authenticate(self):
        """
        Authenticate with the APIC. This method should not be called directly.
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

    def get(self, method, file_format=None, silent=False):
        """
        Get method that adds the necessary parameters and URL.
        :param method:          ACI method name, i.e. what is following apic-url/api/, excluding .json and .xml
        :param file_format:     Format of returned data, either "json", "xml" or None (default)
        :param silent:          Packet will be sent silently, overriding self.verbose
        :return:                A requests response object
        """
        if file_format is None:
            path = self.get_method_path(method)
        else:
            path = self.get_method_path(method, file_format)

        if self.session is None:
            raise SessionError("Cannot send GET request without a session!")

        resp = self.session.get(path, verify=False)
        if self.verbose and not silent:
            print("GET {0}".format(path))
            print("Reponse: {0} {1}".format(resp.status_code, resp.reason))
        return resp

    @staticmethod
    def extract_token(response):
        content = json.loads(response.content)
        return content["imdata"][0]["aaaLogin"]["attributes"]["token"]