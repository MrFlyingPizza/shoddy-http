# CMPT 371 Mini-Project
# By Han Gao, Tosrif Jahan Sakib

import logging

from shoddyhttp import ConcurrentShoddyHttpServer


def main():
    logging.basicConfig(
        format="%(asctime)s - [%(levelname)s]: %(message)s",
        level=logging.INFO
    )

    host = "127.0.0.1"
    port = 80
    logging.info("Creating Multi-Threaded server")
    ConcurrentShoddyHttpServer(host, port, timeout=100).start()
    logging.info("Stopped Multi-Threaded server")


if __name__ == "__main__":
    main()
