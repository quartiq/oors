#!/usr/bin/env python3

import argparse
import os
import asyncio

from artiq.protocols.pc_rpc import simple_server_loop
from artiq import tools

from .oors import OORS


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", help="target host uri (default: '%(default)s')",
                        default="wss://10.32.4.146/core/")
    parser.add_argument("--user", default="guest")
    parser.add_argument("--password", default="")

    tools.simple_network_args(parser, 3276)
    if hasattr(tools, "add_common_args"):
        tools.add_common_args(parser)  # ARTIQ-5
    else:
        tools.verbosity_args(parser)   # ARTIQ-4
    return parser


def main():
    args = get_argparser().parse_args()
    tools.init_logger(args)

    if os.name == "nt":
        asyncio.set_event_loop(asyncio.ProactorEventLoop())
    loop = asyncio.get_event_loop()

    dev = OORS()
    loop.run_until_complete(dev.connect(
        args.uri, user=args.user, password=args.password))

    try:
        loop.run_until_complete(dev.misc())
        simple_server_loop({"oors": dev},
                           tools.bind_address_from_args(args), args.port)
    except KeyboardInterrupt:
        pass
    finally:
        pass  # loop.run_until_complete(dev.disconnect())


if __name__ == "__main__":
    main()
