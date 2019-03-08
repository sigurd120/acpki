from requests import *


def status_to_string(status):
    return str(status.status_code) + " " + status.reason
