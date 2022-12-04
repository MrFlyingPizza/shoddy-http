import logging
from enum import Enum
from socket import socket, AF_INET, SOCK_STREAM
from typing import Tuple, Dict, List

HostAndPort = Tuple[str, str]

Headers = Dict[str, any]


class HttpMethod(Enum):
    """
    HTTP request methods.
    """
    GET = "GET"
    PUT = "PUT"
    HEAD = "HEAD"
    POST = "POST"


class HttpVersion(Enum):
    """
    HTTP protocols.
    """
    HTTP_1_1 = "HTTP/1.1"


class HttpStatusCode(Enum):
    """
    HTTP response status codes.
    """
    OK = 200
    NOT_MODIFIED = 304
    BAD_REQUEST = 300
    NOT_FOUND = 404
    REQUEST_TIMED_OUT = 408


class HttpStatusMessage(Enum):
    """
    HTTP response status messages.
    """
    OK = "OK"
    NOT_MODIFIED = "Not Modified"
    BAD_REQUEST = "Bad Request"
    NOT_FOUND = "Not Found"
    REQUEST_TIMED_OUT = "Request Timed Out"


class HttpResponse:
    """
    Represents an HTTP response.
    """

    def __init__(self, *, version: HttpVersion = HttpVersion.HTTP_1_1, status: HttpStatusCode = HttpStatusCode.OK,
                 headers: Headers = None, data=""):
        """
        Constructs an object representing an HTTP response.
        :param version: The protocol of this response message.
        :param status: The status code of this response message.
        :param headers: The headers of this response message.
        :param data: The data in the response.
        """
        self.version = version
        self.status = status
        self.headers = headers
        self.data = data

    def __build_status_line(self) -> str:
        """
        Builds the string of the status line portion of the response.
        :return: The parsed status line string.
        """
        return f"{self.version.value} {self.status.value} {HttpStatusMessage[self.status.name].value}\n"

    def __build_headers(self) -> str:
        """
        Builds the string of the headers portion of the response.
        If there are no headers, then the empty string is returned.
        :return: The parsed headers string.
        """
        if self.headers is None:
            return ""

        return "\n".join(f"{key}: {value}" for key, value in self.headers.items()) + "\n"

    def to_raw(self) -> str:
        """
        Builds the entire HTTP response string.
        :return: The parsed HTTP response string.
        """
        return f"{self.__build_status_line()}{self.__build_headers()}\n{self.data}"


class HttpRequest:
    """
    Represents an HTTP request.
    """

    def __init__(self, *, method: HttpMethod = HttpMethod.GET, url: str = "",
                 version: HttpVersion = HttpVersion.HTTP_1_1, headers: Headers = None, body: str = ""):
        """
        Constructs an object representing an HTTP request.
        :param method: The HTTP request method of this request.
        :param url: The URL of this request.
        :param version: The HTTP protocol version of this request.
        :param headers: The headers in this HTTP request.
        :param body: The body of this request.
        """
        self.method = method
        self.url = url
        self.version = version
        self.headers = headers
        self.body = body

    def __build_request_line(self):
        """
        Builds the string of the request line portion of this HTTP request.
        :return: The parsed request line string.
        """
        return f"{self.method.value} {self.url} {self.version.value}\n"

    def __build_headers(self):
        """
        Builds the string of the headers portion of the response.
        If there are no headers, then the empty string is returned.
        :return: The parsed headers string.
        """
        if self.headers is None:
            return ""
        return "\n".join(f"{key}: {value}" for key, value in self.headers.items()) + "\n"

    def to_raw(self):
        """
        Builds the entire HTTP request string.
        :return: The parsed HTTP request string.
        """
        return f"{self.__build_request_line()}{self.__build_headers()}\n{self.body}"


def http_request_from_raw(raw_request: str) -> HttpRequest:
    """
    Makes a HttpRequest instance from the given raw HTTP request message.
    :param raw_request: The raw HTTP request message.
    :return: The newly constructed HttpRequest instance.
    """
    top_section: str
    body: str
    top_section, body = raw_request.split("\n\n", maxsplit=1)
    top_lines = top_section.split("\n")

    method, url, version = top_lines[0].split(" ")
    header_lines = top_lines[1:]

    headers: Headers = {}
    for line in header_lines:
        key, value = line.split(": ")
        headers[key] = value

    return HttpRequest(method=HttpMethod(method), url=url, version=HttpVersion(version), headers=headers, body=body)


class ShoddyServer(object):
    """
    HTTP Server class responsible for binding to a socket and listening for connections.
    """

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

    def __handle_connection(self, connection: socket, address: HostAndPort):
        """
        Handles a connection.
        :param connection: The connection instance.
        :param address: The (Host, Port) of the peer.
        """
        logging.info(f"Server - Connected by: {address}")

        connected = True
        while connected:
            data = connection.recv(1024)

            if not data:
                connected = False

            s = data.decode()

            logging.info(f"Received\n'{s}'\nfrom {address}")

            content = ""

            with open("test.html", "r") as file:
                content = file.read()

            headers = {
                "Content-Length": len(content)
            }

            status = 200

            response = f"HTTP/1.1 {status}" + "\n".join(
                f"{key}: {value}" for key, value in headers.items()) + "\n\n" + content

            connection.send(response.encode())

            if s == 'stop':
                connected = False
                self.running = False

    def start(self):
        """
        Start the blocking loops that listens for connections.
        """
        logging.info(f"Starting server with {self.host}:{self.port}")
        self.soc.bind((self.host, self.port))
        self.soc.listen(5)

        self.running = True

        while self.running:
            self.__handle_connection(*self.soc.accept())

        self.soc.close()
        self.running = False


def main():
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(message)s",
        level=logging.INFO
    )

    HOST = "127.0.0.1"
    PORT = 80
    logging.info("Starting server")
    server = ShoddyServer(HOST, PORT, True)
    logging.info("Stopped server")


if __name__ == "__main__":
    main()
