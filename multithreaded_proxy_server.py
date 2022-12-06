# CMPT 371 Mini-Project
# By Han Gao, Tosrif Jahan Sakib
import logging

from shoddyproxy import ShoddyProxy


def main():
    host = "127.0.0.1"
    port = 81
    logging.info("Creating proxy server")
    ShoddyProxy(host, port, ("127.0.0.1", 80)).start()
    logging.info("Stopped proxy server")


if __name__ == "__main__":
    main()
