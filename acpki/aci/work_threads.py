import time, sys
from threading import Thread
from acpki.util.exceptions import SubscriptionError


class StoppableThread(Thread):
    def __init__(self):
        super(StoppableThread, self).__init__()
        self.running = False

    def start(self):
        super(StoppableThread, self).start()
        self.running = True

    def stop(self):
        self.running = False


class WSThread(StoppableThread):
    def __init__(self, ws, callback, sleep_length=1, start=True):
        """
        Create a new WebSocket Thread.
        :param ws:              WebSocket
        :param sub_cb:          Subscription callback method to which received data will be sent
        :param sleep_length:    Time to sleep between each check of the WebSocket
        :param start:           Whether to start the thread upon creation
        """
        self.deamon = True
        self.ws = ws
        self.cb = callback
        self.sleep_length = float(sleep_length)

        self.updated = time.time()
        super(WSThread, self).__init__()

        self.start()

    def run(self):
        while True:
            try:
                time.sleep(self.sleep_length)
                if self.running:
                    opcode, data = self.ws.recv_data()
                    if opcode and data:
                        self.cb(opcode, data)
            except KeyboardInterrupt:
                sys.exit()


class RefreshThread(StoppableThread):
    """
    This thread class ensures that the WebSocket is refreshed at a regular interval.
    """
    def __init__(self, ws, refresh_cb, interval, start=True):
        self.ws = ws
        self.cb = refresh_cb
        self.sub_interval = interval

        self.ws_ttl = self.ws.gettimeout()
        self.updated = time.time()

        # Check time limits for errors
        if self.ws_ttl < self.sub_interval:
            raise SubscriptionError("WebSocket TTL cannot be shorter than refresh interval!")
        elif self.ws_ttl < self.sub_interval - 5:
            print("WARNING: Your subscription interval is less than 5 seconds below the WebSocket TTL. This could lead"
                  "to a WebSocket expiration before it is refreshed.")

        super(RefreshThread, self).__init__()

        self.start()

    def run(self):
        while True:
            if self.running:
                time_diff = time.time() - self.updated
                if time_diff >= self.sub_interval:
                    self.cb()
                    self.updated = time.time()
                    print("Pinging WS to keep connection alive")
                    self.ws.ping()
            time.sleep(1)
