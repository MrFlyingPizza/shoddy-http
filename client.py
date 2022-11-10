from multiprocessing import Pool
from random import randint

from shoddyclient import ShoddyClient


def test_client(stuff: (ShoddyClient, int)):
    client, num = stuff
    for i in range(10):
        client.send(f"Cum {i}".encode())


def main():
    client = ShoddyClient('127.0.0.1', 6969)

    with Pool() as pool:
        pool.map(test_client, [(client, randint(1, 10)) for i in range(5)])


if __name__ == '__main__':
    main()
