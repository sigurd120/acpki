import time
from acpki.aci import ACIAdapter


class PSA:
    def __init__(self):
        self.adapter = ACIAdapter()
        self.epgs = []
        self.contracts = []

        self.main()

    def main(self):
        self.adapter.connect(auto_prepare=True)
        self.epgs = self.adapter.get_epgs(self.sub_cb)

        for epg in self.epgs:
            cons = self.adapter.get_consumed_contracts(epg.name)
            prov = self.adapter.get_provided_contracts(epg.name)
            print("{0} consumes {1} contract(s) and provides {2} contract(s)".format(epg.name, len(cons), len(prov)))

    def sub_cb(self, opcode, data):
        print("PSA EPG CB: {}".format(data))


if __name__ == "__main__":
    psa = PSA()
