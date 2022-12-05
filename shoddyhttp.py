import logging
import os
import shutil

from enum import Enum
from pathlib import Path
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

    UNSUPPORTED = "UNSUPPORTED"


class HttpVersion(Enum):
    """
    HTTP protocols.
    """
    HTTP_1_1 = "HTTP/1.1"

    UNSUPPORTED = "UNSUPPORTED"


class HttpStatusCode(Enum):
    """
    HTTP response status codes.
    """
    OK = 200
    NOT_MODIFIED = 304
    BAD_REQUEST = 300
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    REQUEST_TIMED_OUT = 408


class HttpStatusMessage(Enum):
    """
    HTTP response status messages.
    """
    OK = "OK"
    NOT_MODIFIED = "Not Modified"
    BAD_REQUEST = "Bad Request"
    NOT_FOUND = "Not Found"
    METHOD_NOT_ALLOWED = "Method Not Allowed"
    REQUEST_TIMED_OUT = "Request Timed Out"


class InvalidHttpMethodError(Exception):
    def __init__(self, expected: HttpMethod, actual: HttpMethod,
                 message="The given http method does not match the one expected."):
        self.expected = expected
        self.actual = actual
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} Expected: {self.expected} Actual: {self.actual}"


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

    method_str, url, version_str = top_lines[0].split(" ")
    header_lines = top_lines[1:]

    headers: Headers = {}
    for line in header_lines:
        key, value = line.split(": ")
        headers[key] = value

    method = HttpMethod.UNSUPPORTED
    if method_str in [val.value for val in HttpMethod]:
        method = HttpMethod(method_str)

    version = HttpVersion.UNSUPPORTED
    if version_str in [val.value for val in HttpVersion]:
        version = HttpVersion(version_str)

    return HttpRequest(method=method, url=url, version=version, headers=headers,
                       body=body)


class HttpResponses:
    """
    A class for holding typical responses that can be used repeatedly, like Request Timed Out or Not Found.
    """
    __TIMEOUT_BODY = "REQUEST TIMED OUT."
    TIMEOUT = HttpResponse(status=HttpStatusCode.REQUEST_TIMED_OUT, headers={"Content-Length": len(__TIMEOUT_BODY)},
                           data=__TIMEOUT_BODY)

    __NOT_FOUND_BODY = "NOT FOUND."
    NOT_FOUND = HttpResponse(status=HttpStatusCode.NOT_FOUND, headers={"Content-Length": len(__NOT_FOUND_BODY)},
                             data=__NOT_FOUND_BODY)

    __BAD_REQUEST_BODY = "BAD REQUEST."
    BAD_REQUEST = HttpResponse(status=HttpStatusCode.BAD_REQUEST, headers={"Content-Length": len(__BAD_REQUEST_BODY)},
                               data=__BAD_REQUEST_BODY)

    __SUCCESS_BODY = "SUCCESS."
    OK = HttpResponse(headers={"Content-Length": len(__SUCCESS_BODY)}, data=__SUCCESS_BODY)

    __METHOD_NOT_ALLOWED_BODY = "METHOD NOT ALLOWED"
    METHOD_NOT_ALLOWED = HttpResponse(status=HttpStatusCode.METHOD_NOT_ALLOWED,
                                      headers={"Content-Length": len(__METHOD_NOT_ALLOWED_BODY)},
                                      data=__METHOD_NOT_ALLOWED_BODY)


class ContentHandler:
    def __init__(self, content_dir: str = "/content"):
        """
        Constructs a content handler to operate on content in the given directory.
        :param content_dir: The directory to serve content from. If this directory does not exist, the constructor
        will create it. All paths must be in the form "/{pathname}" where there is no trailing slash.
        :raises OSError: on exception.
        """
        path = Path(content_dir)
        if not path.is_dir():
            self.__log(f"The directory '{str(path)}' does not exist. It will be created.")
            path.mkdir(parents=True)

        self.content_dir = content_dir

    def __make_path(self, path: str):
        """
        Constructs a path from the content path and the given path.
        :param path: The path inside the content path.
        :return: A string that has the content path and the given path concatenated.
        :raises OSError: on exception.
        """
        return self.content_dir + path

    def __log(self, message: str, level: int = logging.INFO):
        """
        Logs message of given level.
        :param message: Message to be logged.
        :param level: Logging level.
        """
        logging.log(level, f"{self.__repr__()}: {message}")

    def retrieve(self, path_str: str) -> str | None:
        """
        Retrieves the string content of a file if it exists, otherwise None.
        :param path_str: The path of the file.
        :return: Returns the contents of a file if it exists, or None if it doesn't.
        :raises OSError: on exception.
        """
        path_str = self.__make_path(path_str)

        path = Path(path_str)

        self.__log(f"Handling retrieval of '{str(path)}'")

        result: str | None = None
        if path.is_file():
            result = path.read_text()

        return result

    def create(self, path_str: str, content: str) -> bool:
        """
        Saves given string contents to the file specified by the path if it doesn't exist.
        :param path_str: The path to save the contents at.
        :param content: The contents of the file.
        :return: True if successfully saved, False if not found.
        :raises OSError: on exception.
        """
        path_str = self.__make_path(path_str)

        path = Path(path_str)

        self.__log(f"Handling creation of '{str(path)}'")

        if path.is_file():
            return False

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

        return True

    def delete(self, path_str: str) -> bool:
        """
        Deletes the given path if it exists. Can be both files or directories.
        :param path_str: The path to be deleted.
        :return: True if successful, False if not found.
        :raises OSError: on exception.
        """
        path_str = self.__make_path(path_str)

        path = Path(path_str)

        self.__log(f"Handling deletion of '{str(path)}'")

        if path.is_file():
            path.unlink()
            return True

        if path.is_dir():
            path.rmdir()
            shutil.rmtree(path)
            return True

        return False

    def replace(self, path_str: str, content: str) -> bool:
        """
        Replaces the contents of the file at the specified path if it exists.
        :param path_str: The path of the file to replace contents at.
        :param content: The contents to be replaced with.
        :return: True if successfully replaced, False if not found.
        :raises OSError: on exception.
        """
        path_str = self.__make_path(path_str)

        path = Path(path_str)

        self.__log(f"Handling replacement of '{str(path)}'")

        if path.is_file():
            path.unlink()
            path.write_text(content)
            return True

        return False


class RequestHandler:
    """
    An instance of this class handles an HTTP request through an open connection.
    The instance is invalidated if the connection closes.
    """
    __INVALID_METHOD_MESSAGE = "This request handler cannot handle the given request based on its request method."

    def __init__(self, connection: socket, address: HostAndPort, content_handler: ContentHandler, timeout=60):
        """
        The open connection to handle the request using.
        :param connection: The socket of the open connection.
        :param timeout: How long to wait for data before sending timeout and closing connection.
        :param content_handler: The instance of content handler to service content requests using.
        """
        if not content_handler:
            raise ValueError("The content handler must be provided.")

        self.connection = connection
        self.address = address
        self.timeout = timeout
        self.content_handler = content_handler

    def __log(self, message: str, level: int = logging.INFO):
        """
        Logs message of given level.
        :param message: Message to be logged.
        :param level: Logging level.
        """
        logging.log(level, f"{self.__repr__()}: {message}")

    def __receive_request(self, conn: socket) -> HttpRequest | None:
        """
        Receive all data from a connection, and send timeout the connection if no activity for too long.
        :param conn: Socket connection to receive data from.
        :return: All bytes of the data received. None if request timeout.
        """
        s = conn.recv(8192).decode()

        self.__log(f"Received from {self.address}:\n{s}\n")

        return http_request_from_raw(s)

    def __handle_get_request(self, request: HttpRequest):
        """
        Handles an HTTP request with the GET method.
        It gets a file from the file system indicated by the URL path and sends it back.
        Send 404 Not Found if not found by the path.
        :param request: The request object.
        """
        self.__log(f"Handling GET request from {self.address}")
        if request.method != HttpMethod.GET:
            raise InvalidHttpMethodError(HttpMethod.GET, request.method, self.__INVALID_METHOD_MESSAGE)

        content = self.content_handler.retrieve(request.url)

        response = HttpResponses.NOT_FOUND
        if content is not None:
            headers = {
                "Content-Length": len(content)
            }

            response = HttpResponse(headers=headers, data=content)

        self.__send_response(response)

    def __handle_put_request(self, request: HttpRequest):
        """
        Handles an HTTP request with the PUT method.
        It should replace a file specified by the URL path.
        Send 404 Not Found if not found by the path.
        :param request: The request object.
        """
        self.__log(f"Handling PUT request from {self.address}")

        if request.method != HttpMethod.PUT:
            raise InvalidHttpMethodError(HttpMethod.PUT, request.method, self.__INVALID_METHOD_MESSAGE)

        success = self.content_handler.replace(request.url, request.body)

        response = HttpResponses.NOT_FOUND
        if success:
            response = HttpResponses.OK

        self.__send_response(response)

    def __handle_post_request(self, request: HttpRequest):
        """
        Handles an HTTP request with the POST method.
        It should save the contents of the body to the file system.
        It should send 400 Bad Request if the operation fails.
        :param request: The request object.
        """
        self.__log(f"Handling POST request from {self.address}")

        if request.method != HttpMethod.POST:
            raise InvalidHttpMethodError(HttpMethod.POST, request.method, self.__INVALID_METHOD_MESSAGE)

        success = self.content_handler.create(request.url, request.body)

        response = HttpResponses.BAD_REQUEST
        if success:
            response = HttpResponses.OK

        self.__send_response(response)

    def __handle_delete_request(self, request: HttpRequest):
        """
        Handles an HTTP request with the DELETE method.
        It should remove a file specified by the URL path.
        Send 404 Not Found if not found by the path.
        :param request: The request object.
        """
        self.__log(f"Handling DELETE request from {self.address}")

        if request.method != HttpMethod.DELETE:
            raise InvalidHttpMethodError(HttpMethod.DELETE, request.method, self.__INVALID_METHOD_MESSAGE)

        success = self.content_handler.delete(request.url)

        response = HttpResponses.NOT_FOUND
        if success:
            response = HttpResponses.OK

        self.__send_response(response)

    def __handle_unsupported_request(self, request: HttpRequest):
        """
        Handles an HTTP request of an unexpected method.
        :param request: The request object.
        """
        self.__log(f"Handling an unsupported request from {self.address}")
        self.__send_response(HttpResponses.METHOD_NOT_ALLOWED)

    def __handle_request(self, request: HttpRequest):
        """
        Handles an HTTP request..
        :param request: The HTTP request.
        """
        match request.method:

            case HttpMethod.GET:

                return self.__handle_get_request(request)

            case HttpMethod.PUT:

                return self.__handle_put_request(request)

            case HttpMethod.POST:

                return self.__handle_post_request(request)

            case HttpMethod.DELETE:

                return self.__handle_delete_request(request)

            case _:

                return self.__handle_unsupported_request(request)

    def __send_response(self, response: HttpResponse):
        r = response.to_raw()

        self.__log(f"Sending response to {self.address}:\n{response.to_raw()}")

        self.connection.send(r.encode())

    def handle(self):
        request = self.__receive_request(self.connection)
        self.__handle_request(request)

        self.connection.close() # Each connection is only used for 1 request, thus close the connection then done.


class ShoddyServer(object):
    """
    HTTP Server class responsible for binding to a socket and listening for connections.
    """

    def __init__(self, host: str, port: int, *, timeout=60, content_dir="/content"):
        """
        Creates a new shoddy server to listen for connections.
        Instantiates a content handler with the given content dir to pass to request handlers.
        :param host: The IP address to use for the server.
        :param port: The port to use for the server.
        :param timeout: The number of seconds to wait for receiving before sending a timeout response.
        """
        self.host = host
        self.port = port
        self.soc = socket(family=AF_INET, type=SOCK_STREAM)
        self.timeout = timeout
        self.content_handler = ContentHandler(os.getcwd() + content_dir)

    def start(self):
        """
        Start the blocking loops that listens for connections.
        """
        logging.info(f"Starting server with {self.host}:{self.port}")
        self.soc.bind((self.host, self.port))
        self.soc.listen(5)

        running = True

        while running:
            socket, address = self.soc.accept()
            socket.settimeout(self.timeout)
            RequestHandler(socket, address, self.content_handler, timeout=self.timeout).handle()

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
    ShoddyServer(host, port, timeout=100).start()
    logging.info("Stopped server")


if __name__ == "__main__":
    main()
