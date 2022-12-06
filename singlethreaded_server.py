import logging

from shoddyhttp import ShoddyHttpServer


def main():
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(message)s",
        level=logging.INFO
    )

    host = "127.0.0.1"
    port = 80
    logging.info("Creating Single-Threaded server")
    ShoddyHttpServer(host, port, timeout=100).start()
    logging.info("Stopped Single-Threaded server")


if __name__ == "__main__":
    main()
