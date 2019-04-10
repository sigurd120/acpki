

class Subscription:
    def __init__(self, sid, method, callback=None, active=True):
        self.sid = sid
        self.method = method
        self.callback = callback
        self.active = active

    def refresh(self):
        raise NotImplementedError()
