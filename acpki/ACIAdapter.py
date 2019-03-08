from acitoolkit import acitoolkit
from util import NetworkHelper


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self):
        # Configuration parameters
        self.apic_url = "https://sandboxapicdc.cisco.com"
        self.username = "admin"
        self.password = "ciscopsdt"
        self.connection_timeout = 1800  # Seconds or None

        # Set initial values
        self.verbose = True
        self.session = None
        self.config()

    def config(self):
        """
        Set up the required parameters and authenticate with the APIC. Should only be called on initial setup of the
        ACIAdapter.
        """
        self.authenticate()

    def authenticate(self):
        """
        Authenticate with the APIC using the username and password provided
        :return: True if authentication was successful and False otherwise
        """
        self.session = acitoolkit.Session(self.apic_url, self.username, self.password)

        status = self.session.login(self.connection_timeout)
        if status.ok:
            if self.verbose:
                print("Authentication successful! (" + NetworkHelper.status_to_string(status) + ")")
            return True
        else:
            if self.verbose:
                print("Authentication failed. (" + NetworkHelper.status_to_string(status) + ")")
            return False
