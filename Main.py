from acpki.ACIAdapter import ACIAdapter


class Main:
    def __init__(self):
        self.aci_adapter = None

    def run(self):
        self.aci_adapter = ACIAdapter()


if __name__ == "__main__":
    main = Main()
    main.run()
