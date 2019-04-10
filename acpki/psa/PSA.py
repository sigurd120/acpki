import time
from acpki.aci import ACIAdapter


class PSA:
    def __init__(self):
        self.adapter = ACIAdapter()
        self.epgs = []

        self.main()

    def main(self):
        self.adapter.connect()
        self.epgs = self.adapter.get_epgs(self.sub_cb)

    def sub_cb(self, opcode, data):
        print("PSA EPG CB: {}".format(data))


if __name__ == "__main__":
    psa = PSA()
