import time
from acpki.aci import ACIAdapter


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

    def contract_cb(self, opcode, data):
        print("{0} {1}".format(opcode, data))

    def sub_cb(self, opcode, data):
        print("PSA EPG CB: {}".format(data))


if __name__ == "__main__":
    psa = PSA()
