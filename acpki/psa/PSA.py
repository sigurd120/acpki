import json
from acpki.aci import ACIAdapter
from acpki.models import EPG
from acpki.util.exceptions import NotFoundError


class PSA:
    """
    Policy Security Adapter (PSA): This class acts as the main bridge between Cisco ACI and the PKI part of AC-PKI. It
    requests information about endpoints, policies and subscribes to any changes in these data. The PSA also maintains
    an internal model of the most critical data in the Cisco APIC, so it can continue operations even if the APIC is
    unavailable for a while during runtime.
    """
    def __init__(self):
        self.verbose = True
        self.epgs = []
        self.contracts = []

        self.adapter = ACIAdapter()

        self.main()

    def main(self):
        self.adapter.connect(auto_prepare=True)

        # Load EPGs and contracts
        self.epgs = self.adapter.get_epgs(self.sub_cb)
        for epg in self.epgs:
            epg.consumes = self.adapter.get_consumed_contracts(epg.name, callback=self.contract_cb)
            epg.provides = self.adapter.get_provided_contracts(epg.name, callback=self.contract_cb)

    def get_contracts(self, origin, destination):
        """
        Get all contracts between the specified origin and destination EPG.
        :param origin:          Origin of the contract (consumer)
        :param destination:     Destination of the contract (provider)
        :return:                List of contracts
        """
        origin_epg = None
        destination_epg = None
        contracts = []

        # Find EPG matches
        for epg in self.epgs:
            if epg.dn == origin.dn:
                origin_epg = epg
            elif epg.dn == destination.dn:
                destination_epg = epg

        if origin_epg is None or destination_epg is None:
            print("ERROR: One or both of the certificates do not exist in the PSA context. Please ensure that the"
                  "certificate names are identical to the ones in Cisco ACI. ")
            return False

        # Find matching contract
        for contract in destination_epg.provides:
            if contract in origin_epg.consumes:
                contracts.append(contract)
        return None if len(contracts) == 0 else contracts

    def validate_contract(self, contract):
        raise NotImplementedError

    def connection_allowed(self, origin, destination):
        contracts = self.get_contracts(origin, destination)
        for con in contracts:
            if self.validate_contract(con):
                return True
        return False

    def contract_cb(self, opcode, data):
        # TODO: Handle this to update any changes in contracts upon callback
        print("{0} {1}".format(opcode, data))

    def sub_cb(self, opcode, data):
        """
        Subscription callback method, which is called whenever a subscription receives a new update. The method will
        forward the data to its corresponding sub callback method, e.g. for EPGs or contracts.
        :param opcode:      Unique identifier that corresponds to the socket with which the callback was received
        :param data:        JSON data with the item(s) that have been updated
        :return:
        """
        json_obj = json.loads(data)
        subId = json_obj["subscriptionId"]

        # Iterate through updates in subscription data and call specific callback method
        for item in json_obj["imdata"]:
            if "fvAEPg" in item:
                self.epg_cb(item["fvAEPg"]["attributes"])
            else:
                pass  # TODO: Add other types of callbacks

    def epg_cb(self, attrs):
        """
        This callback method is called if a subscription callback concerns an EPG, and will create, modify or delete an
        existing endpoint in the local self.epgs list.
        :param attrs:   The attributes received from the JSON object in the subscription
        :return:
        """
        if attrs["status"] == "created":
            # Add EPG to local list
            epg = EPG(attrs["dn"], attrs["name"])
            if self.verbose:
                print("Endpoint group \"{0}\" was added to the PSA.".format(epg.name))
            self.epgs.append(epg)
        elif attrs["status"] == "modified":
            # Modify existing EPG
            epg = EPG(attrs["dn"], attrs["name"])
            for i, epg_local in enumerate(self.epgs):
                if epg_local.equals(epg):
                    self.epgs[i] = epg
                    if self.verbose:
                        print("Endpoint group \"{0}\" was modified.".format(epg.name))
                    break
        elif attrs["status"] == "deleted":
            # Delete EPG from local list
            for i, epg_local in enumerate(self.epgs):
                if epg_local.dn == attrs["dn"]:
                    name = self.epgs[i].name
                    del self.epgs[i]
                    if self.verbose:
                        print("Endpoint group \"{0}\" was deleted.".format(name))
                    break
        elif self.verbose:
            # Unknown status
            print("Skipped unknown operation \"{0}\" for EPG: {1}".format(attrs["status"], attrs["dn"]))


if __name__ == "__main__":
    psa = PSA()
