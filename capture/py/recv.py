from reciever import ThreadedUDPHandler, ThreadedUDPServer


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=12351)
    parser.add_argument("-o", type=argparse.FileType("wb"), default="-")
    args = parser.parse_args()

    with ThreadedUDPServer(("0.0.0.0", args.port), ThreadedUDPHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            import threading

            def kill_me_please(server):
                server.shutdown()

            threading.Thread(target=kill_me_please, args=(server,))
