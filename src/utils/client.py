import socket
import threading


class LocalBroadcastClient:
    """Receive some data from devices connected on the same network"""

    def __init__(self, discovery_port: int) -> None:
        self.port = discovery_port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.received_data: list[bytes] = []
        self.is_receiving = False

    def start_receiving(self):
        self.is_receiving = True
        threading.Thread(target=self.receive, daemon=True).start()

    def close(self):
        self.is_receiving = False
        self.client.close()

    def receive(self):
        self.client.sendto("DISCOVER".encode(), ("255.255.255.255", self.port))

        while self.is_receiving:
            response, _ = self.client.recvfrom(1024)
            self.received_data.append(response)


class UDPClient:
    """Sends some data to the UDP Server and receives data sent by other clients from the server"""

    def __init__(self, server_ip: str, server_port: int) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_addr = (server_ip, server_port)
        self.is_alive = False
        self.received_data: bytes = b""

    def start(self):
        self.socket.connect(self.server_addr)
        self.is_alive = True
        threading.Thread(target=self.listen, daemon=True).start()

    def send(self, data: bytes):
        self.socket.sendto(data, self.server_addr)

    def listen(self):
        while self.is_alive:
            self.received_data = self.socket.recv(1024)
