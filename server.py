from shoddyserver import ShoddyServer


def main():
    print("Starting server")
    server = ShoddyServer('127.0.0.1', 6969, True)
    print("Stopped server")


if __name__ == '__main__':
    main()
