from acitoolkit import acitoolkit
import websocket


class Subscriber:
    ws = None

    def __init__(self, host, token):
        self.host = host
        self.token = token

        self.setup()

    def setup(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(url=self.host)