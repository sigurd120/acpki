import json, requests
from requests.auth import HTTPBasicAuth
from requests.cookies import RequestsCookieJar
from acitoolkit import acitoolkit
from acpki.util import NetworkHelper
from acpki.util.custom_exceptions import InvalidTokenError


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self):
        # Configuration parameters
        self.apic_base_url = "sandboxapicdc.cisco.com"
        self.apic_web_url = "https://" + self.apic_base_url
        self.username = "admin"
        self.password = "ciscopsdt"
        self.connection_timeout = 1800  # Seconds or None

        self.token_path = "private/token.txt"

        # Set initial values
        self.verbose = True
        self.session = None
        self.token = None
        self.cookie = None
        self.auth_cookie = None

        # Configure
        self.config()

    def config(self):
        """
        Set up the required parameters and authenticate with the APIC. Should only be called on initial setup of the
        ACIAdapter.
        """
        self.refresh_session()

    def get(self, method, format="json", headers=None, params=None):
        """
        Standard GET request to the APIC.
        :param method:      Method name (following APIC/api/... in the full API call)
        :param format:      json or xml
        :param headers:     Additional headers, must be of type dictionary
        :param params:      Additional GET parameters, separated with "&", example: "param1=value1&param2=value2"
        :return:            Returns a HTTP(S) response object as defined by requests library
        """
        path = "{0}/api/{1}.{2}".format(self.apic_web_url, method, format)
        if params:
            path = path + "?" + params

        if headers is None:
            headers = {}

        cookies = RequestsCookieJar()
        # TODO: If this works the domain should be taken from the config instead
        cookies.set("APIC-cookie", self.token, domain=".sandboxapic.cisco.com", path="/")


        headers["content-type"] = "application/json"

        if "https://" in path and self.token is None:
            raise InvalidTokenError("Invalid token! Could not send GET request using HTTPS without successful "
                                    "authentication.")

        print("Token: {}".format(self.token))
        return requests.get(path, headers=headers, cookies=cookies, verify=False)

    def refresh_session(self):
        """
        This method retrieves auth token from file and checks its validity. If the token does not exist, it calls the
        authenticate() method to get a new one. Using this method instead of authenticate() directly reduces network
        traffic and overall load on the APIC.
        :return:    True if successful, False otherwise
        """
        success = False
        token = None

        # Try to read token from file
        try:
            with open(self.token_path, "r") as f:
                self.set_token(str(f.readline()))
        except IOError as e:
            print("Could not read token from file. Error: {}".format(e))

        # Test message
        resp = self.get("mo/uni/tn-Heroes", params="subscription=no")
        print("Response: {}".format(NetworkHelper.status_to_string(resp)))

        # Error handling
        if resp.ok:
            print("Successfully resumed session with existing token.")
        elif resp.status_code == 403:
            print("Logging you back in...")
            self.authenticate()
        else:
            print("Unknown error occured. Please try again or contact a sysadmin. ")

    def set_token(self, token):
        self.token = token

    def authenticate(self, save_to_file=True):
        """
        Authenticate with the APIC using the username and password provided
        :return: True if authentication was successful and False otherwise
        TODO: It would make sense to just use requests lib here, not acitoolkit...
        """
        self.session = acitoolkit.Session(self.apic_web_url, self.username, self.password)
        success = False

        response = self.session.login(self.connection_timeout)
        if response.ok:
            if self.verbose:
                print("Authentication successful! (" + NetworkHelper.status_to_string(response) + ")")

            # Get token
            content = json.loads(response.content)
            try:
                self.set_token(content["imdata"][0]["aaaLogin"]["attributes"]["token"])
            except KeyError:
                print("Could not find token in authentication response. ")
                return False

            # Save to file
            if save_to_file:
                try:
                    with open(self.token_path, "w") as f:
                        f.write(self.token)
                except IOError as eio:
                    print("Could not write token to file. Error: {}".format(eio))
                else:
                    print("Token with length {} was successfully written to file.".format(len(self.token)))

            return True
        else:
            if self.verbose:
                print("Authentication failed. ({})".format(NetworkHelper.status_to_string(response)))
            return False


if __name__ == "__main__":
    aciadapter = ACIAdapter()