import sys, os, time, json
from acpki.aci import ACISession
from acpki.models import EPG, EPGUpdate, Tenant
from acpki.config import CONFIG
from acpki.util.exceptions import RequestError, NotFoundError, ConnectionError


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self):
        # Setup
        self.tenant_name = CONFIG["apic"]["tn-name"]
        self.ap_name = CONFIG["apic"]["ap-name"]
        self.session = ACISession(verbose=True)

    def connect(self, auto_prepare=True):
        # Connect to APIC
        self.session.connect()
        time.sleep(3)
        if auto_prepare:
            self.prepare_environment()

    def prepare_environment(self):
        # Check if the tenant exists
        res = self.session.get("node/mo/uni/tn-{0}.json".format(self.tenant_name))
        if res.ok:
            content = json.loads(res.content)
            if int(content["totalCount"]) == 0:
                # Create tenant
                tenant = Tenant(self.tenant_name)
                res = self.session.post("mo/uni", tenant.to_json(), file_format="json")
                if not res.ok:
                    raise RequestError("Could not create tenant. Response: {0} {1}".format(res.status_code, res.reason))
        else:
            raise ConnectionError("Could not get tenant from the APIC. ({0} {1}".format(res.status_code, res.reason))

        # Check if the AP exists



    def disconnect(self):
        self.session.disconnect()

    def get_epgs(self, sub_cb):
        """
        Get all EPGs from the APIC and subscribe to changes by defining a callback method. All changes will be submitted
        to this callback method.
        :param callback:    Callback method to which EPGUpdate objects will be sent upon submission to the ACIAdapter
                            (Default: None)
        :return:            All EPGs that exist at request time
        """
        # Define params and url
        params = {
            "query-target": "children",
            "target-subtree-class": "fvAEPg",
            "order-by": "fvAEPg.name|asc",
            #"query-target-filter": "eq(fvAEPg.isAttrBasedEPg,\"false\")",
        }

        url = "node/mo/uni/tn-{0}/ap-{1}".format(self.tenant_name, self.ap_name)

        # Send request and verify response
        resp = self.session.get(url, "json", sub_cb=sub_cb, subscribe=True, params=params)
        if resp.ok:
            # Load initial EPGs in the current AP
            content = json.loads(resp.content)
            epgs = []
            for item in content["imdata"]:
                # Add each EPG to the epgs array
                json_epg = item["fvAEPg"]["attributes"]
                epg = EPG(json_epg["dn"], json_epg["name"])
                epgs.append(epg)
            return epgs
        else:
            raise RequestError("Could not get EPGs from the APIC. Please check the request URL, GET parameters, "
                               "configuration and that the APIC is available before trying again.")

    def load_epgs(self):
        raise NotImplementedError

    def json_to_epg_update(self, json_update):
        update = json.loads(json_update)


if __name__ == "__main__":
    aciadapter = ACIAdapter()
    try:
        aciadapter.connect()
        time.sleep(3)
    except KeyboardInterrupt:
        print("Keyboard interrupt. Shutting down...")
        aciadapter.disconnect()
