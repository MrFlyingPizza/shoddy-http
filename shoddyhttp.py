import logging
from enum import Enum
from socket import socket, AF_INET, SOCK_STREAM
from typing import Tuple, Dict

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
    DELETE = "DELETE"


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
        return f"{self.version.value} {self.status.value} {HttpStatusMessage[self.status.name].value}\r\n"

    def __build_headers(self) -> str:
        """
        Builds the string of the headers portion of the response.
        If there are no headers, then the empty string is returned.
        :return: The parsed headers string.
        """
        if self.headers is None or len(self.headers) <= 0:
            return ""

        return "\r\n".join(f"{key}: {value}" for key, value in self.headers.items()) + "\r\n"

    def to_raw(self) -> str:
        """
        Builds the entire HTTP response string.
        :return: The parsed HTTP response string.
        """
        return f"{self.__build_status_line()}{self.__build_headers()}\r\n{self.data}"


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
        return f"{self.method.value} {self.url} {self.version.value}\r\n"

    def __build_headers(self):
        """
        Builds the string of the headers portion of the response.
        If there are no headers, then the empty string is returned.
        :return: The parsed headers string.
        """
        if self.headers is None or len(self.headers) <= 0:
            return ""

        return "\r\n".join(f"{key}: {value}" for key, value in self.headers.items()) + "\r\n"

    def to_raw(self):
        """
        Builds the entire HTTP request string.
        :return: The parsed HTTP request string.
        """
        return f"{self.__build_request_line()}{self.__build_headers()}\r\n{self.body}"


def http_request_from_raw(raw_request: str) -> HttpRequest:
    """
    Makes a HttpRequest instance from the given raw HTTP request message.
    :param raw_request: The raw HTTP request message.
    :return: The newly constructed HttpRequest instance.
    """
    top_section: str
    body: str
    top_section, body = raw_request.split("\r\n\r\n", maxsplit=1)
    top_lines = top_section.split("\r\n")

    method, url, version = top_lines[0].split(" ")
    header_lines = top_lines[1:]

    headers: Headers = {}
    for line in header_lines:
        key, value = line.split(": ")
        headers[key] = value

    return HttpRequest(method=HttpMethod(method), url=url, version=HttpVersion(version), headers=headers, body=body)


class HttpResponses:
    """
    A class for holding typical responses that can be used repeatedly, like Request Timed Out or Not Found.
    """
    TIMEOUT = HttpResponse(status=HttpStatusCode.REQUEST_TIMED_OUT)
    TIMEOUT_BYTES = TIMEOUT.to_raw().encode()

    NOT_FOUND = HttpResponse(status=HttpStatusCode.NOT_FOUND)
    NOT_FOUND_BYTES = NOT_FOUND.to_raw().encode()


class ConnectionHandler:
    """
    An instance of this class handles one open HTTP connection. The instance is invalidated if the connection closes.
    """

    def __init__(self, connection: socket, address: HostAndPort, timeout=5):
        """
        The open connection to handle the request using.
        :param connection: The socket of the open connection.
        :param timeout: How long to wait for data before sending timeout and closing connection.
        """
        self.connection = connection
        self.address = address
        self.timeout = timeout

    def __receive_request(self, conn: socket) -> HttpRequest | None:
        """
        Receive all data from a connection, and send timeout the connection if no activity for too long.
        :param conn: Socket connection to receive data from.
        :return: All bytes of the data received. None if request timeout.
        """
        chunks = []
        receiving = True
        while receiving:
            data = None
            try:
                conn.settimeout(self.timeout)
                data = conn.recv(2048)
                conn.settimeout(None)

                chunks.append(data)

            except TimeoutError:
                conn.settimeout(None)
                conn.send(HttpResponses.TIMEOUT_BYTES)
                conn.close()

            if not data:
                receiving = False

        if len(chunks) <= 0:
            return None

        s = b''.join(chunks).decode()

        logging.info(f"Received:\n{s}\nfrom:\n{self.address}")

        return http_request_from_raw(s)

    def __handle_get_request(self, request: HttpRequest) -> HttpResponse:
        """
        Handles an HTTP request with the GET method.
        It gets a file from the file system indicated by the URL path and sends it back.
        Send 404 Not Found if not found by the path.
        :param request: The request object.
        :return: An HTTP response to send back to the client.
        """
        if request.method != HttpMethod.GET:
            raise f"GET request handler cannot handle request of {request.method}"

        # TODO: implement
        ...

    def __handle_put_request(self, request: HttpRequest) -> HttpResponse:
        """
        Handles an HTTP request with the PUT method.
        It should replace a file specified by the URL path.
        Send 404 Not Found if not found by the path.
        :param request: The request object.
        :return: An HTTP response to send back to the client.
        """
        if request.method != HttpMethod.PUT:
            raise f"PUT request handler cannot handle request of {request.method}"

        # TODO: implement
        ...

    def __handle_post_request(self, request: HttpRequest) -> HttpResponse:
        """
        Handles an HTTP request with the POST method.
        It should save the contents of the body to the file system.
        It should send 400 Bad Request if a file already exists by the given path.
        :param request: The request object.
        :return: An HTTP response to send back to the client.
        """
        if request.method != HttpMethod.POST:
            raise f"POST request handler cannot handle request of {request.method}"

        # TODO: implement
        ...

    def __handle_head_request(self, request: HttpRequest) -> HttpResponse:
        """
        Handles an HTTP request with the HEAD method.
        :param request: The request object.
        :return: An HTTP response to send back to the client.
        """
        if request.method != HttpMethod.HEAD:
            raise f"HEAD request handler cannot handle request of {request.method}"

        # TODO: implement
        ...

    def __handle_delete_request(self, request: HttpRequest) -> HttpResponse:
        """
        Handles an HTTP request with the DELETE method.
        It should remove a file specified by the URL path.
        Send 404 Not Found if not found by the path.
        :param request: The request object.
        :return: An HTTP response to send back to the client.
        """
        if request.method != HttpMethod.DELETE:
            raise f"DELETE request handler cannot handle request of {request.method}"

        # TODO: implement
        ...

    def __handle_unsupported_request(self, request: HttpRequest) -> HttpResponse:
        """
        Handles an HTTP request of an unexpected method.
        :param request: The request object.
        :return: An HTTP response to send back to the client.
        """

        # TODO: implement
        ...

    def handle(self):
        """
        Handles a connection.
        :param conn: The connection instance.
        :param address: The (Host, Port) of the peer.
        """
        request = self.__receive_request(self.connection)

        match request.method:
            case HttpMethod.GET:
                self.__handle_get_request(request)
            case HttpMethod.PUT:
                self.__handle_put_request(request)
            case HttpMethod.HEAD:
                self.__handle_head_request(request)
            case HttpMethod.POST:
                self.__handle_post_request(request)
            case HttpMethod.DELETE:
                self.__handle_delete_request(request)
            case _:
                self.__handle_unsupported_request(request)


class ShoddyServer(object):
    """
    HTTP Server class responsible for binding to a socket and listening for connections.
    """

    def __init__(self, host: str, port: int, *, timeout=5):
        """
        Creates a new shoddy server to listen for connections.
        :param host: The IP address to use for the server.
        :param port: The port to use for the server.
        :param timeout: The number of seconds to wait for receiving before sending a timeout response.
        """
        self.host = host
        self.port = port
        self.soc = socket(family=AF_INET, type=SOCK_STREAM)
        self.timeout = timeout

    def start(self):
        """
        Start the blocking loops that listens for connections.
        """
        logging.info(f"Starting server with {self.host}:{self.port}")
        self.soc.bind((self.host, self.port))
        self.soc.listen(5)

        running = True

        while running:
            ConnectionHandler(*self.soc.accept()).handle()

        self.soc.close()
        running = False


def main():
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(message)s",
        level=logging.INFO
    )

    host = "127.0.0.1"
    port = 80
    logging.info("Creating server")
    ShoddyServer(host, port).start()
    logging.info("Stopped server")


if __name__ == "__main__":
    main()
