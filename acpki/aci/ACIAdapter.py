import sys, os, time, json
from acpki.aci import ACISession
from acpki.models import Tenant, AP, EPG, EPGUpdate, Contract
from acpki.config import CONFIG
from acpki.util.exceptions import RequestError, NotFoundError, ConnectionError


class ACIAdapter:
    """
    The ACIAdapter works as the bridge between AC-PKI and Cisco ACI. It sets up a subscription with the APIC and the
    tenant in question.
    """

    def __init__(self, verbose=True):
        # Arguments
        self.verbose = verbose

        # Setup
        self.tenant_name = CONFIG["apic"]["tn-name"]
        self.ap_name = CONFIG["apic"]["ap-name"]

        # Create session
        self.session = ACISession(verbose=self.verbose)

    def connect(self, auto_prepare):
        """
        Connect to the APIC.
        :param auto_prepare:    Creates the tenant and AP if they do not exist
        :return:
        """
        self.session.connect()
        time.sleep(3)
        if auto_prepare:
            self.prepare_environment()

    def prepare_environment(self):
        # Check if the tenant exists
        res = self.session.get("node/mo/uni/tn-{0}".format(self.tenant_name))
        if res.ok:
            content = json.loads(res.content)
            if int(content["totalCount"]) == 0:
                # Create tenant
                print("Creating Tenant {0}".format(self.tenant_name))
                tenant = Tenant(self.tenant_name)
                res = self.session.post("mo/uni", tenant.to_json())
                if res.ok:
                    print("Tenant successfully created.")
                else:
                    raise RequestError("Could not create tenant. Response: {0} {1}".format(res.status_code, res.reason))
        else:
            raise ConnectionError("Could not get tenant from the APIC. ({0} {1}".format(res.status_code, res.reason))

        # Check if the AP exists
        res1 = self.session.get("node/mo/uni/tn-{0}/ap-{1}".format(self.tenant_name, self.ap_name))
        if res1.ok:
            # 200 OK
            content = json.loads(res1.content)
            if int(content["totalCount"]) == 0:
                # Create AP
                print("Creating AP {0}".format(self.ap_name))
                ap = AP(self.ap_name)
                res2 = self.session.post("mo/uni/tn-{0}".format(self.tenant_name), ap.to_json())
                if res2.ok:
                    print("AP successfully created.")
                else:
                    raise RequestError("Could not create AP {0}. Response: {1} {2}"
                                       .format(self.ap_name, res2.status_code, res2.reason))
        else:
            raise ConnectionError("Could not get AP from the APIC. ({0} {1}".format(res1.status_code, res1.reason))

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

    def get_contracts(self, provider, cls, callback):
        """
        Get all contracts provided by the provider EPG specified
        :param provider:    The providing EPG
        :param cls:         Subtree class, must be fvRsProv for provided contracts or fvRsCons for consumed contracts
        :param callback:    The callback method to which subscription data will be forwarded
        :return:
        """
        if cls != "fvRsProv" and cls != "fvRsCons":
            raise ValueError("Invalid value for argument cls")

        path = "node/mo/uni/tn-{0}/ap-{1}/epg-{2}".format(self.tenant_name, self.ap_name, provider)
        params = {
            "query-target": "subtree",
            "target-subtree-class": cls
        }
        subscribe = callback is not None
        contracts = []

        json_resp = self.session.get(path, "json", subscribe=subscribe, params=params, silent=True, sub_cb=callback)
        content = json.loads(json_resp.content)

        for item in content["imdata"]:
            json_contract = item[cls]["attributes"]
            contract = Contract(json_contract["uid"], json_contract["tnVzBrCPName"])
            contracts.append(contract)

        return contracts

    def get_provided_contracts(self, provider, callback=None):
        return self.get_contracts(provider, "fvRsProv", callback)

    def get_consumed_contracts(self, provider, callback=None):
        return self.get_contracts(provider, "fvRsCons", callback)

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
