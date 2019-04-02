from acitoolkit import acitoolkit
from util import NetworkHelper


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self):
        # Configuration parameters
        self.apic_address = "sandboxapicdc.cisco.com"
        self.username = "admin"
        self.password = "ciscopsdt"
        self.connection_timeout = 1800  # Seconds or None

        # Set initial values
        self.verbose = True
        self.session = None
        self.apic_api_url = self.get_apic_web_url(True)
        self.apic_ws_url = self.get_apic_ws_url(True)

        # Configure
        self.config()

    def config(self):
        """
        Set up the required parameters and authenticate with the APIC. Should only be called on initial setup of the
        ACIAdapter.
        """
        self.authenticate()

    def get_apic_web_url(self, secure=True):
        if secure:
            url = "https://" + self.apic_address
        else:
            url = "http://" + self.apic_address
        return url

    def get_apic_ws_url(self, secure=True):
        if secure:
            url = "wss://" + self.apic_address
        else:
            url = "ws://" + self.apic_address
        return url

    def authenticate(self):
        """
        Authenticate with the APIC using the username and password provided
        :return: True if authentication was successful and False otherwise
        """
        self.session = acitoolkit.Session(self.apic_web_url, self.username, self.password)

        status = self.session.login(self.connection_timeout)
        if status.ok:
            if self.verbose:
                print("Authentication successful! (" + NetworkHelper.status_to_string(status) + ")")
            return True
        else:
            if self.verbose:
                print("Authentication failed. ({})".format(NetworkHelper.status_to_string(status)))
            return False
