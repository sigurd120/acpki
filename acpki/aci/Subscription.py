

class Subscription:
    def __init__(self, sid, method, active=True):
        self.sid = sid
        self.method = method
        self.active = active

    def refresh(self):
        raise NotImplementedError()
