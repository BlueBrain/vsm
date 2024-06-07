import asyncio
from argparse import ArgumentParser
from dataclasses import dataclass
from logging import INFO, Logger
from ssl import PROTOCOL_TLS_SERVER, SSLContext

from aiohttp import web
from aiohttp_middlewares.cors import cors_middleware

from .logger import create_logger
from .settings import BASE_HOST, CERT_CRT, CERT_KEY


@dataclass
class Settings:
    port: int
    host: str = BASE_HOST
    secure: bool = False


async def run_application(name: str, default_port: int, logger: Logger, routes: list[web.RouteDef]) -> None:
    settings = parse_argv(name, default_port)

    logger.info(f"{name} settings: {settings}")

    ssl_context = create_ssl_context(settings.secure)

    application = web.Application(
        logger=create_logger("aiohttp", INFO),
        middlewares=[cors_middleware(allow_all=True)],
    )

    application.router.add_routes(
        [
            web.get("/healthz", healthcheck),
            *routes,
        ]
    )

    runner = web.AppRunner(application)
    await runner.setup()

    site = web.TCPSite(runner, settings.host, settings.port, ssl_context=ssl_context)

    logger.info(f"{name} running at {settings.host}:{settings.port}")

    await site.start()

    try:
        await asyncio.Future()
    finally:
        await runner.cleanup()


def parse_argv(description: str, default_port: int) -> Settings:
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        default=default_port,
        help="port to bind to",
    )
    parser.add_argument(
        "--address",
        dest="host",
        type=str,
        default=BASE_HOST,
        help="address to bind to",
    )
    parser.add_argument("--ssl", dest="ssl", action="store_true", help="force SSL")
    settings = Settings(default_port)
    parser.parse_args(namespace=settings)
    return settings


def create_ssl_context(secure: bool) -> SSLContext | None:
    if not secure:
        return None
    context = SSLContext(PROTOCOL_TLS_SERVER)
    context.load_cert_chain(CERT_CRT, CERT_KEY)
    return context


async def healthcheck(request: web.Request) -> web.Response:
    return web.HTTPOk()
