class Contract:
    """
    Model class representing a Cisco ACI Contract
    """
    def __init__(self, uid, name, dn):
        self.uid = uid
        self.name = name
        self.dn = dn
