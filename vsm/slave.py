#!/usr/bin/python3
import argparse
import asyncio
import logging
import ssl

from aiohttp import web
from aiohttp_swagger import setup_swagger

from . import logger, sentry, settings, websocket_proxy
from .utils import setup_cors


async def start_webapp(args):
    if args.ssl:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.check_hostname = False
        ssl_context.load_cert_chain(settings.CERT_CRT, settings.CERT_KEY)
    else:
        ssl_context = None

    app = web.Application()
    app.router.add_routes(
        [
            web.get(
                "/{job_id}/{service:renderer|backend}",
                websocket_proxy.WebSocketProxy().ws_handler,
            )
        ]
    )

    setup_cors(app)
    webapp_runner = web.AppRunner(app, access_log=None)

    if settings.SWAGGER_ENABLED:
        setup_swagger(app)

    await webapp_runner.setup()
    site = web.TCPSite(webapp_runner, args.address, args.port, ssl_context=ssl_context)
    logging.info(
        f"VMM webscocket worker running at {args.address}:{args.port}", extra=dict(detail="test")
    )
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
    parser = argparse.ArgumentParser(description="websocket proxy application")
    parser.add_argument(
        "--port", dest="port", type=int, default=settings.BASE_PORT, help="port to bind to"
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
