import requests, pickle, sys, os
import urllib3
from acpki.util.custom_exceptions import SessionError


class ACISession:
    def __init__(self):
        # Configuration
        self.apic_base_url = "sandboxapicdc.cisco.com"
        self.apic_web_url = "https://" + self.apic_base_url
        self.username = "admin"
        self.password = "ciscopsdt"
        self.cookie_file = "private/cookie.txt"
        self.session = None
        self.connected = False
        self.verbose = True

        # Setup and connect
        self.setup()
        self.connect()

    def setup(self):
        # Disable certificate verification -- this is not provided by Cisco ACI
        # TODO: Look into whether certificate can be validated against Cisco's root certificate
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get_method_path(self, method, file_format="json"):
        return self.apic_web_url + "/api/" + method + "." + file_format

    def connect(self):
        if self.resume_session():
            print("Successfully resumed saved session.")
        else:
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
        self.session = requests.Session()
        login = {"aaaUser":{"attributes": {"name": self.username, "pwd": self.password}}}
        path = self.get_method_path("aaaLogin")
        resp = self.session.post(path, json=login, verify=False)

        if self.verbose and resp.ok:
            print("Successfully logged in.")
        else:
            print("Error: {0} {1}".format(resp.status_code, resp.reason))
            print("Authentication with the Cisco APIC failed. Terminating...")
            sys.exit(1)

        if self.cookie_file:
            try:
                with open(self.cookie_file, "wb") as f:
                    pickle.dump(self.session.cookies, f)
            except IOError:
                print("Could not save session. Continuing without persistency...")

        return resp

    def check_connection(self):
        """
        Checks whether the class is successfully connected with the APIC and sets the self.connected parameter
        accordingly.
        :return:    Current connection status (True or False)
        """
        resp = self.get("mo/uni/tn-common")  # Get common tenant (which should always exist in Cisco ACI
        self.connected = resp.ok is True
        if self.verbose:
            print("Connection status: {0} {1}".format(resp.status_code, resp.reason))
        return self.connected

    def get(self, method, file_format=None):
        """
        Get method that adds the necessary parameters and URL.
        :param method:          ACI method name, i.e. what is following apic-url/api/, excluding .json / .xml
        :param file_format:     Format of returned data, either "json", "xml" or None (default)
        :return:                A requests response object
        """
        if file_format is None:
            path = self.get_method_path(method)
        else:
            path = self.get_method_path(method, file_format)

        if self.session is None:
            raise SessionError("Cannot send GET request without a session!")

        resp = self.session.get(path, verify=False)
        if self.verbose:
            print("GET {0}".format(path))
            print("Reponse: {0} {1}".format(resp.status_code, resp.reason))
        return resp


if __name__ == "__main__":
    sess = ACISession()