# CMPT 371 Mini-Project
# By Han Gao, Tosrif Jahan Sakib
import logging
from socket import socket, AF_INET, SOCK_STREAM

from shoddyhttp import RequestHandler, HttpRequest, HttpResponse, HostAndPort, ContentHandler, http_response_from_raw, \
    ConcurrentShoddyHttpServer


class ProxyRequestHandler(RequestHandler):

    def __init__(self, connection: socket, address: HostAndPort, content_handler: ContentHandler,
                 destination: HostAndPort, timeout=60):
        """
        Constructs a request handler for the proxy.
        :param connection: The socket connection with the client.
        :param address: The address of the client.
        :param content_handler: The handler to operate on content.
        :param destination: The address of the origin server to forward requests to.
        :param timeout: How long to timeout requests.
        """
        super().__init__(connection, address, content_handler, timeout)
        self.destination = socket(family=AF_INET, type=SOCK_STREAM)
        self.destination.connect(destination)

    def __forward(self, request: HttpRequest) -> HttpResponse:
        """
        Forwards an HTTP request to its appropriate destination.
        :param request: The request to be forwarded.
        :return: The response from the destination server.
        """
        self.destination.send(request.to_raw().encode())
        raw_response = self.destination.recv(8192).decode()
        self._log(f"Forwarding request from {self.address}:\n{raw_response}")

        return http_response_from_raw(raw_response)

    def _handle_request(self, request: HttpRequest):
        response = self.__forward(request)
        self.send_response(response)


class ShoddyProxy(ConcurrentShoddyHttpServer):

    def __init__(self, host: str, port: int, destination: HostAndPort, *, timeout=60, content_dir="/content"):
        super().__init__(host, port, timeout=timeout, content_dir=content_dir)
        self.destination = destination

    def _handler_callback(self, conn: socket, address: HostAndPort):
        ProxyRequestHandler(conn, address, content_handler=self.content_handler, destination=self.destination,
                            timeout=self.timeout).handle()


def main():
    host = "127.0.0.1"
    port = 81
    logging.info("Creating proxy server")
    ShoddyProxy(host, 81, ("127.0.0.1", 80)).start()


if __name__ == "__main__":
    main()
