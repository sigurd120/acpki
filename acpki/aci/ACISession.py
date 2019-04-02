import requests, pickle, sys, os
import urllib3
from acpki.util.custom_exceptions import SessionError


class ACISession:
    session = None

    def __init__(self):
        self.apic_base_url = "sandboxapicdc.cisco.com"
        self.apic_web_url = "https://" + self.apic_base_url
        self.username = "admin"
        self.password = "ciscopsdt"
        self.cookie_file = "private/cookie.txt"

        self.setup()

    def setup(self):
        # Disable certificate verification -- this is not provided by Cisco ACI
        # TODO: Look into whether certificate can be validated against Cisco's root certificate
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if self.resume_session():
            print("Successfully resumed saved session.")
        else:
            print("Authenticating...")
            self.authenticate()

    def get_method_path(self, method, file_format="json"):
        return self.apic_web_url + "/api/" + method + "." + file_format

    def resume_session(self):
        """
        If AC-PKI has recently been logged in, this method will resume the session by loading the
        :return:
        """
        if self.cookie_file and os.path.exists(self.cookie_file):
            # Load cookies from file
            session = requests.session()
            with open(self.cookie_file, "rb") as f:
                session.cookies.update(pickle.load(f))

            self.session = session
            return self.test_connection()

    def authenticate(self):
        self.session = requests.Session()
        login = {"aaaUser":{"attributes": {"name": self.username, "pwd": self.password}}}
        path = self.get_method_path("aaaLogin")
        res = self.session.post(path, json=login, verify=False)

        if res.ok:
            print("Successfully logged in.")
        else:
            print("Error: {0} {1}".format(res.status_code, res.reason))
            print("Authentication with the Cisco APIC failed. Terminating...")
            sys.exit(1)

        if self.cookie_file:
            try:
                with open(self.cookie_file, "wb") as f:
                    pickle.dump(self.session.cookies, f)
            except IOError:
                print("Could not save session. Continuing without persistency...")

    def test_connection(self):
        res = self.get("mo/uni/tn-common")
        return res.ok

    def get(self, method, file_format=None):
        if file_format is None:
            path = self.get_method_path(method)
        else:
            path = self.get_method_path(method, file_format)

        if self.session is None:
            raise SessionError("Cannot send GET request without a session!")
        resp = self.session.get(path, verify=False)

        return resp


if __name__ == "__main__":
    sess = ACISession()