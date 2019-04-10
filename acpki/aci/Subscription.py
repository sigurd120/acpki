

class Subscription:
    def __init__(self, subscriber, sub_id, method, callback=None, active=True):
        self.subscriber = subscriber
        self.sub_id = sub_id
        self.method = method
        self.callback = callback
        self.active = active