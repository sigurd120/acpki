import time
from threading import Thread


class WSThread(Thread):
    def __init__(self, ws):
        Thread.__init__(self)
        self.deamon = True
        self.ws = ws
        self.start()

    def run(self):
        while True:
            time.sleep(1)
            opcode, data = self.ws.recv_data()
            if opcode and data:
                print("WS {0}: {1}".format(opcode, data))
            else:
                print("No data received")
