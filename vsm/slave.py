import argparse
import asyncio
import logging
import ssl

from aiohttp import web
from aiohttp_swagger import setup_swagger

from . import logger, sentry, settings
from .utils import setup_cors
from .websocket_proxy import WebSocketProxy


async def healthcheck(request: web.Request) -> web.Response:
    return web.Response(status=200)


async def main(args):
    logger.configure()

    if settings.ENVIRONMENT:
        sentry.set_up()

    if args.ssl:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.check_hostname = False
        ssl_context.load_cert_chain(settings.CERT_CRT, settings.CERT_KEY)
    else:
        ssl_context = None

    proxy = WebSocketProxy()

    app = web.Application()

    routes = [
        web.get("/healthz", healthcheck),
        web.get("/{job_id}/{service:renderer|backend}", proxy.ws_handler),
    ]

    app.router.add_routes(routes)

    setup_cors(app)
    runner = web.AppRunner(app, access_log=None)

    if settings.SWAGGER_ENABLED:
        setup_swagger(app)

    await runner.setup()

    site = web.TCPSite(runner, args.address, args.port, ssl_context=ssl_context)

    logging.info(f"VMM webscocket worker running at {args.address}:{args.port}")

    await site.start()

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        await runner.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="websocket proxy application")
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
    asyncio.run(main(parser.parse_args()))
