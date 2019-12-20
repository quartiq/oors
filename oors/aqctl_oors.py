#!/usr/bin/env python3

import argparse
import os
import asyncio

from sipyco.pc_rpc import Server
from sipyco import common_args

from sipyco.common_args import (
    simple_network_args, init_logger_from_args as init_logger,
    bind_address_from_args, verbosity_args)


from .oors import OORS


def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", help="target host uri (default: '%(default)s')",
                        default="wss://ms1/core/")
    parser.add_argument("--user", default="guest")
    parser.add_argument("--password", default="")

    simple_network_args(parser, 3276)
    verbosity_args(parser)
    return parser


def main():
    args = get_argparser().parse_args()
    init_logger(args)

    if os.name == "nt":
        asyncio.set_event_loop(asyncio.ProactorEventLoop())
    loop = asyncio.get_event_loop()

    dev = OORS()

    async def run():
        await dev.connect(args.uri, user=args.user, password=args.password)
        await dev.misc()
        server = Server({"oors": dev}, None, True)
        await server.start(bind_address_from_args(args), args.port)
        try:
            await server.wait_terminate()
        except KeyboardInterrupt:
            pass
        finally:
            await server.stop()
    loop.run_until_complete(run())

if __name__ == "__main__":
    main()
