import socket
import threading

import ujson


class LocalBroadcastServer:
    """Broadcast some data to devices connected on the same network"""

    def __init__(self, discovery_port: int, broadcast_data: bytes) -> None:
        self.port = discovery_port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", self.port))
        self.broadcast_data = broadcast_data
        self.is_broadcasting = False

    def start(self):
        self.is_broadcasting = True
        threading.Thread(target=self.listen, daemon=True).start()

    def close(self):
        self.is_broadcasting = False
        self.server.close()

    def listen(self):
        while self.is_broadcasting:
            message, addr = self.server.recvfrom(1024)
            if message.decode() == "DISCOVER":
                self.server.sendto(self.broadcast_data, addr)


class UDPServer:
    """Listens for incoming clients and broadcasts received data to other clients"""

    def __init__(self, port: int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = set()
        self.socket.bind((socket.gethostbyname(socket.gethostname()), port))
        self.is_listening = False

    def start(self):
        self.is_listening = True
        threading.Thread(target=self.echo_listen, daemon=True).start()

    def echo_listen(self):
        all_clients_data = {}
        while self.is_listening:
            data, addr = self.socket.recvfrom(1024)
            self.clients.add(addr)
            all_clients_data[addr] = ujson.loads(data.decode())

            if len(all_clients_data) == len(self.clients):
                for client in self.clients:
                    data = all_clients_data.copy()
                    data.pop(client)
                    self.socket.sendto(
                        ujson.dumps(list(data.values())).encode(), client
                    )
