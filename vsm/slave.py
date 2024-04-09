import argparse
import asyncio
import logging
import ssl

from aiohttp import ClientSession, web
from aiohttp_middlewares.cors import cors_middleware

from . import logger, settings
from .websocket_proxy import WebSocketProxy


async def healthcheck(request: web.Request) -> web.Response:
    return web.HTTPOk()


async def main():
    parser = argparse.ArgumentParser(description="VSM proxy application")
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=settings.SLAVE_PORT,
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

    args = parser.parse_args()

    logger.configure()

    if args.ssl:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.check_hostname = False
        ssl_context.load_cert_chain(settings.CERT_CRT, settings.CERT_KEY)
    else:
        ssl_context = None

    async with ClientSession() as session:
        proxy = WebSocketProxy(session)

        app = web.Application(
            logger=logging.root,
            middlewares=[cors_middleware(allow_all=True)],
        )

        routes = [
            web.get("/healthz", healthcheck),
            web.get("/{job_id}/{service:renderer|backend}", proxy.ws_handler),
        ]

        app.router.add_routes(routes)

        runner = web.AppRunner(app, access_log=None)

        await runner.setup()

        site = web.TCPSite(runner, args.address, args.port, ssl_context=ssl_context)

        logging.info(f"VSM slave running at {args.address}:{args.port}")

        await site.start()

        try:
            await asyncio.Future()
        finally:
            await runner.cleanup()


def run_slave() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run_slave()
