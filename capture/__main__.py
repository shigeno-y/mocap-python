if __name__ == "__main__":
    import argparse

    from .reciever import ThreadedUDPHandler, ThreadedUDPServer

    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-port", type=int, default=12351)
    args = parser.parse_args()

    with ThreadedUDPServer(("0.0.0.0", args.listen_port), ThreadedUDPHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            import threading

            def kill_me_please(server):
                server.shutdown()

            threading.Thread(target=kill_me_please, args=(server,))
