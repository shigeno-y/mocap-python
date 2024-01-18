def run_udp(args):
    from .reciever import ThreadedUDPHandler, ThreadedUDPServer

    with ThreadedUDPServer(("0.0.0.0", args.listen_port), ThreadedUDPHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            import threading

            def kill_me_please(server):
                server.shutdown()

            threading.Thread(target=kill_me_please, args=(server,))


def run_convert(args):
    from .composer import composeFromBVH

    if args.output is None:
        args.output = args.input.with_suffix("")

    composeFromBVH(args.input, args.output, args.stride)


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    udp = subparsers.add_parser("udp")
    udp.add_argument("--listen-port", type=int, default=12351)
    udp.set_defaults(func=run_udp)

    convert = subparsers.add_parser("convert")
    convert.add_argument("input", type=Path)
    convert.add_argument("-o", "--output", type=Path, metavar="OUTPUT", default=None)
    convert.add_argument("--stride", type=int, metavar="STRIDE", default=6000)
    convert.set_defaults(func=run_convert)

    args = parser.parse_args()
    args.func(args)
