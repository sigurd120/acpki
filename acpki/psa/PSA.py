import json, string, random, os
from acpki.aci import ACIAdapter
from acpki.models import EPG, CertificateValidationRequest, Contract
from acpki.util.randomness import random_string
from acpki.util.exceptions import NotFoundError
from acpki.config import CONFIG


class PSA:
    """
    Policy Security Adapter (PSA): This class acts as the main bridge between Cisco ACI and the PKI part of AC-PKI. It
    requests information about endpoints, policies and subscribes to any changes in these data. The PSA also maintains
    an internal model of the most critical data in the Cisco APIC, so it can continue operations even if the APIC is
    unavailable for a while during runtime.
    """
    def __init__(self):
        self.verbose = CONFIG["verbose"]
        self.epgs = []
        self.ous = {}
        self.ous_file = CONFIG["psa"]["ous-file"]

        self.adapter = ACIAdapter()
        self.main()

    def main(self):

        self.setup()

        self.adapter.connect(auto_prepare=True)

        self.load_epgs_and_contracts()

    def setup(self):
        # Check that OUs file exists and load
        if os.path.exists(self.ous_file):
            # Load OUs
            with open(self.ous_file, "r") as f:
                data = f.readlines()
                for line in data:
                    vals = line.split(";")
                    if len(vals) != 3:
                        continue
                    self.ous[vals[0]] = (vals[1], vals[2])
        else:
            open(self.ous_file, "w")

    def get_epg(self, epg_name):
        for epg in self.epgs:
            if epg.name == epg_name:
                return epg
        if self.verbose:
            print("Warning: Did not find the EPG: {}".format(epg_name))
        return None

    def load_epgs_and_contracts(self):
        # Load EPGs and contracts
        self.epgs = self.adapter.get_epgs(self.sub_cb)
        for epg in self.epgs:
            epg.consumes = self.adapter.get_consumed_contracts(epg.name, callback=self.sub_cb)
            epg.provides = self.adapter.get_provided_contracts(epg.name, callback=self.sub_cb)

    def get_contracts(self, origin, destination):
        """
        Get all contracts between origin and destination endpoints' EPGs.
        :param origin:          Origin EP of the contract (consumer)
        :param destination:     Destination EP of the contract (provider)
        :return:                List of contracts
        """
        contracts = []

        # Find contracts consumed by origin and provided by destination
        if origin.epg is not None:
            for cons in origin.epg.consumes:
                for prov in destination.epg.provides:
                    if cons.uid == prov.uid:
                        contracts.append(cons)

        # Find contracts provided by origin and consumed by destination
        if destination.epg is not None:
            for prov in origin.epg.provides:
                for cons in destination.epg.consumes:
                    if prov.uid == cons.uid:
                        contracts.append(prov)

        return contracts

    def validate_contract(self, contract):
        raise NotImplementedError

    def validate_certificate(self, cvr):
        """
        Validate a certificate based on a Certificate Validation Request (CVR).
        :param cvr:     The CVR to validate
        :return:        True if valid, False otherwise
        """

        # Check contract between EPGs
        if not self.connection_allowed(cvr.origin, cvr.destination):
            return False

        # Check OU
        subject = cvr.cert.get_subject()
        valid_ous = []

        # Load valid OUs from dictionary
        for key, val in self.ous.iteritems():
            if val == (cvr.origin.name, cvr.destination.name):
                valid_ous.append(key)

        subj_ou = subject.OU
        valid = subj_ou in valid_ous

        return valid

    def connection_allowed(self, origin, destination):
        """
        Connection is allowed if there exists one or more contracts between the origin and destination EPG.
        :param origin:          The origin endpoint for communications
        :param destination:     The destination endpoint for communications
        :return:                True if allowed, False otherwise
        """
        return len(self.get_contracts(origin, destination)) > 0

    def register_ou(self, eps):
        """
        Register a new OU and store the provided tuple of endpoints in the OUs dictionary. The OU returned from this
        method should be used in the OU subject field of the certificate issued.
        :param eps:     Tuple containing the origin and destination endpoint, respectively
        :return:        The OU with which the tuple was registered in the dictionary
        """
        # Check value of eps parameter
        if not isinstance(eps, tuple) or len(eps) != 2:
            raise ValueError("Endpoint must be tuple of length 2.")

        # Check if request is already registered
        for key, val in self.ous.iteritems():
            if val == eps:
                if self.verbose:
                    print("OU {0} already contained endpoints {1} and {2}".format(key, eps[0], eps[1]))
                return key  # Return the OU for which the request was found

        # Not found - create
        ou = random_string(32)  # Generate random string, no need to check for duplicates... P(Collision) =~ 2.3e+57
        self.ous[ou] = eps

        # Save to file
        with open(self.ous_file, "a") as f:
            f.write("{0};{1};{2}\n".format(ou, eps[1], eps[2]))

        # Print and return
        if self.verbose:
            print("Registered new OU {0} between EPs {1} and {2}".format(ou, eps[0], eps[1]))
        return ou

    def remove_ou(self, ou):
        """
        Remove the given OU from dict.
        :param ou:      OU to delete
        :return:        True if OU was found, False otherwise
        """
        return self.ous.pop(ou, None) is not None

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
                # Endpoint groups updated
                self.epg_cb(item["fvAEPg"]["attributes"])
            elif "fvRsProv" in item:
                # Provided contracts updated
                self.contract_cb("prov", item["fvRsProv"]["attributes"])
            elif "fvRsCons" in item:
                # Consumed contracts updated
                self.contract_cb("cons", item["fvRsCons"]["attributes"])
            else:
                print("Unknown subscription callback: {}".format(item))

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
            name = attrs["name"] if "name" in attrs else None
            epg = EPG(attrs["dn"], name)  # TODO: Find out how to get name from DN
            for i, epg_local in enumerate(self.epgs):
                if epg_local.equals(epg):
                    if epg.name is None:
                        epg.name = self.epgs[i].name  # Workaround for when the name is not sent along with the EPG
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

    def contract_cb(self, action, attrs):
        if attrs["status"] == "created":
            # Create contract
            con = Contract(attrs["uid"], attrs["tnVzBrCPName"], attrs["dn"])
            epg_name = attrs["dn"].split("/")[3][4:]  # Workaround to extract the EPG name from contract DN
            found = False
            for epg in self.epgs:
                if epg.name == epg_name:
                    found = True
                    if action == "prov":
                        epg.provides.append(con)
                    else:
                        epg.consumes.append(con)
            if not found:
                # Reload EPGs and contracts
                print("Error! Could not find EPG {} and could therefore not append new contract from callback."
                      .format(epg_name))
                self.load_epgs_and_contracts()
        elif attrs["status"] == "deleted":
            # Delete contract
            con_dn = attrs["dn"]  # On deletion contracts only have DN set and not "tnVzBrCPName"
            epg_name = con_dn.split("/")[3][4:]  # Workaround to extract EPG name from contract DN
            found = False
            for epg in self.epgs:
                if epg.name == epg_name:
                    # Found the correct EPG
                    if action == "cons":
                        # Delete consumed contract
                        for i, con in enumerate(epg.consumes):
                            if con.dn == con_dn:
                                found = True
                                epg.consumes.pop(i)
                    else:
                        # Delete provided contract
                        for i, con in enumerate(epg.provides):
                            if con.dn == con_dn:
                                found = True
                                epg.provides.pop(i)
            if not found:
                print("Deleting contract from EPG {} failed because it was not found.".format(epg_name))
        elif attrs["updated"]:
            pass  # No action required
        else:
            print("Unknown status skipped for contract callback: {}".format(attrs["status"]))


if __name__ == "__main__":
    psa = PSA()
