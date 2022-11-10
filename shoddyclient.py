from socket import socket, AF_INET, SOCK_STREAM


class ShoddyClient(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.soc = socket(family=AF_INET, type=SOCK_STREAM)
        self.soc.connect((self.host, self.port))

    def send(self, data):
        self.soc.sendall(data)
        data = self.soc.recv(1024)
        print(f"Received: '{repr(data)}'")
