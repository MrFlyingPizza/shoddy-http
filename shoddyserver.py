from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread


class ShoddyServer(object):
    def __init__(self, host: str, port: int, start=False):
        """
        Creates a new shoddy server to listen for connections.
        :param host: The IP address to use for the server.
        :param port: The port to use for the server.
        :param start: Whether to start the server immediately
        """
        self.host = host
        self.port = port
        self.soc = socket(family=AF_INET, type=SOCK_STREAM)
        self.running = start

        if start:
            self.start()

    def __handle_connection(self, connection: socket, address: str):

        print(f"Server - Connected by: {address}")

        connected = True
        while connected:
            data = connection.recv(1024)

            if not data:
                connected = False

            s = repr(data)

            print(f"Received '{s}' from {address}")

            connection.sendall(data)

            if s == 'stop':
                self.running = False

    def start(self):
        print(f"Starting server with {self.host}:{self.port}")
        self.soc.bind((self.host, self.port))
        self.soc.listen(5)

        self.running = True

        while self.running:
            Thread(target=self.__handle_connection, args=self.soc.accept()).start()

        self.soc.close()
        self.running = False
