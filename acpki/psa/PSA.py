import time
from acpki.aci import ACIAdapter


class PSA:
    def __init__(self):
        self.adapter = ACIAdapter()
        self.epgs = []

        self.main()

    def main(self):
        self.adapter.connect()
        self.adapter.set_epg_cb(self.epg_cb)  # Set the callback method
        self.epgs = self.adapter.get_epgs()

    def epg_cb(self, epgs):
        print("PSA EPG CB: {}".format(epgs))


if __name__ == "__main__":
    psa = PSA()
