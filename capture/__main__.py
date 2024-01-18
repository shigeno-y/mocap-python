def run_udp(args):
    from capture import reciever

    reciever.WRITER_OF_CHOICE = args.writer
    reciever.WRITER_OPTIONS = dict(**vars(args))

    with reciever.ThreadedUDPServer(("0.0.0.0", args.listen_port), reciever.ThreadedUDPHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            import threading

            def kill_me_please(server):
                server.shutdown()

            threading.Thread(target=kill_me_please, args=(server,))


def run_convert(args):
    from capture.composer import composeFromBVH

    if args.output_base is None:
        args.output_base = args.input.with_suffix("")

    composeFromBVH(args.input, args.output_base, args.stride)


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from capture import reciever

    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers()

    udp = subparsers.add_parser("udp")
    udp.add_argument("--listen-port", type=int, default=12351)
    udp.add_argument("--writer", choices=reciever.WRITERS.keys(), default="usd")
    udp.add_argument("-o", "--output-base", type=Path, metavar="OUTPUT", default=None)
    udp.add_argument("--stride", type=int, metavar="STRIDE", default=600)
    udp.set_defaults(func=run_udp)

    convert = subparsers.add_parser("convert")
    convert.add_argument("input", type=Path)
    convert.add_argument("-o", "--output-base", type=Path, metavar="OUTPUT", default=None)
    convert.add_argument("--stride", type=int, metavar="STRIDE", default=6000)
    convert.set_defaults(func=run_convert)

    args = parser.parse_args()
    args.func(args)
