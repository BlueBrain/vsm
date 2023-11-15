import argparse
import asyncio
import logging
import os
import ssl

from aiohttp import ClientSession, TCPConnector, web
from aiohttp_swagger import setup_swagger

from . import logger, sentry, settings
from .allocator import JobAllocator
from .aws_allocator import AwsAllocator
from .scheduler import JobScheduler
from .unicore_allocator import UnicoreAllocator
from .utils import setup_cors


def create_allocator(name: str, session: ClientSession) -> JobAllocator:
    if name == "UNICORE":
        return UnicoreAllocator(session)
    if name == "AWS":
        return AwsAllocator()
    raise ValueError(f"Invalid job allocator {name}")


async def healthcheck(request: web.Request) -> web.Response:
    return web.Response(status=200)


async def main(args):
    logger.configure()

    if settings.ENVIRONMENT:
        sentry.set_up()

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

    connector = TCPConnector(ssl=ssl.create_default_context(cafile=settings.UNICORE_CA_FILE if ca_exists else None))

    async with ClientSession(connector=connector) as session:
        allocator = create_allocator(settings.JOB_ALLOCATOR, session)
        scheduler = JobScheduler(allocator)

        app = web.Application()

        routes = [
            web.get("/healthz", healthcheck),
            web.post("/start", scheduler.start),
            web.get("/status/{job_id:[^{}]+}", scheduler.get_status),
        ]

        app.router.add_routes(routes)
        setup_cors(app)

        runner = web.AppRunner(app, access_log=None)

        if settings.SWAGGER_ENABLED:
            setup_swagger(app)

        await runner.setup()

        site = web.TCPSite(runner, args.address, args.port, ssl_context=ssl_context)

        logging.info(f"VSM master running at {args.address}:{args.port}")

        await site.start()

        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            await runner.cleanup()


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
    asyncio.run(main(parser.parse_args()))
