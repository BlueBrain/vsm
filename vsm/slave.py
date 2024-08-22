import asyncio

from aiohttp import ClientSession, web

from .application import run_application
from .db_init import create_db_connector
from .logger import create_logger
from .settings import SLAVE_PORT
from .websocket_proxy import WebSocketProxy


async def main():
    logger = create_logger("VSM_SLAVE")

    connector = create_db_connector()

    async with ClientSession() as session:
        proxy = WebSocketProxy(session, connector, logger)

        routes = [
            web.get("/{job_id}/renderer", proxy.ws_handler),
        ]

        await run_application("VSM proxy", SLAVE_PORT, logger, routes)


def run_slave() -> None:
    asyncio.run(main())
