import time
from acpki.aci import ACIAdapter
from acpki.util.exceptions import NotFoundError


class PSA:
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
        print("PSA EPG CB: {}".format(data))


if __name__ == "__main__":
    psa = PSA()
