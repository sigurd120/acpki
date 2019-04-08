import time
from threading import Thread


class WSThread(Thread):
    def __init__(self, ws, sleep_length=1):
        """
        Create a new WebSocket Thread.
        :param ws:              WebSocket
        :param sleep_length:    Time to sleep between each check of the WebSocket
        """
        Thread.__init__(self)
        self.deamon = True
        self.ws = ws
        self.sleep_length = float(sleep_length)

        self.updated = time.time()
        self.start()

    def run(self):
        while True:
            time.sleep(self.sleep_length)
            opcode, data = self.ws.recv_data()
            if opcode and data:
                print("WS {0}: {1}".format(opcode, data))
            else:
                print("No data received")


class RefreshThread(Thread):
    def __init__(self, ws, refresh_cb, interval):
        Thread.__init__(self)
        self.ws = ws
        self.cb = refresh_cb
        self.sub_interval = interval
        self.ws_ttl = self.ws.gettimeout()
        self.updated = time.time()

        print("Refresh thread created with interval {0} and WS TTL {1}".format(self.sub_interval, self.ws_ttl))

        self.start()

    def run(self):
        while True:
            time_diff = time.time() - self.updated
            if time_diff >= self.sub_interval:
                self.cb()
                self.updated = time.time()
                print("Pinging WS to keep connection alive")
                self.ws.ping()
            time.sleep(1)
