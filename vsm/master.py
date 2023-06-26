#!/usr/bin/python3
import argparse
import asyncio
import logging
import os
import ssl

from aiohttp import ClientSession, TCPConnector, web
from aiohttp_swagger import setup_swagger

from . import logger, sentry, settings
from .unicore_handler import UnicoreHandler
from .unicore_scheduler import UnicoreScheduler
from .utils import setup_cors


async def start_webapp(args):
    if args.ssl:
        logging.info("Enabling SSL")
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.check_hostname = False
        ssl_context.load_cert_chain(settings.CERT_CRT, settings.CERT_KEY)
    else:
        ssl_context = None

    ca_exists = os.path.exists(settings.UNICORE_CA_FILE)
    if ca_exists:
        logging.info(f"Using CA file: {settings.UNICORE_CA_FILE}")
    conn = TCPConnector(
        ssl=ssl.create_default_context(cafile=settings.UNICORE_CA_FILE if ca_exists else None)
    )
    UnicoreHandler().set_session(ClientSession(connector=conn))

    app = web.Application()
    handler = UnicoreScheduler()

    scheduler_routes = [
        web.post("/start", handler.start),
        web.get("/status/{job_id:[^{}]+}", handler.get_status),
    ]

    app.router.add_routes(scheduler_routes)
    setup_cors(app)

    webapp_runner = web.AppRunner(app, access_log=None)

    if settings.SWAGGER_ENABLED:
        setup_swagger(app)

    await webapp_runner.setup()
    site = web.TCPSite(webapp_runner, args.address, args.port, ssl_context=ssl_context)
    logging.info(f"VMM master running at {args.address}:{args.port}")
    await site.start()
    return webapp_runner


def main(args):
    if settings.ENVIRONMENT:
        sentry.set_up()

    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(start_webapp(args))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(runner.cleanup())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BBP MOOC proxy application")
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=settings.BASE_PORT,
        help="port to bind to",
    )
    parser.add_argument(
        "--address",
        dest="address",
        type=str,
        help="address to bind to",
        default=settings.BASE_HOST,
    )
    parser.add_argument("--ssl", dest="ssl", action="store_true", help="force SSL")
    main(parser.parse_args())
