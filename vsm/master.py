import asyncio
import os
import ssl
from contextlib import suppress
from logging import Logger

from aiohttp import ClientSession, TCPConnector, web

from .allocator import FakeAllocator, JobAllocator
from .application import run_application
from .authenticator import Authenticator
from .aws_allocator import AwsAllocator
from .db import create_db_connector
from .logger import create_logger
from .scheduler import JobScheduler
from .settings import JOB_ALLOCATOR, MASTER_PORT, RECREATE_DB, UNICORE_CA_FILE
from .unicore_allocator import UnicoreAllocator


def create_allocator(name: str, session: ClientSession, logger: Logger) -> JobAllocator:
    if name == "UNICORE":
        logger.warn("Unicore deprecated")
        return UnicoreAllocator(session)
    if name == "AWS":
        return AwsAllocator(session, logger)
    if name == "TEST":
        return FakeAllocator(logger)
    raise ValueError(f"Invalid job allocator {name}")


async def main():
    logger = create_logger("VSM_MASTER")

    connector = create_db_connector()

    if RECREATE_DB:
        async with await connector.connect() as connection:
            await connection.recreate_table()

    cafile = None
    if os.path.exists(UNICORE_CA_FILE):
        logger.info(f"Using CA file: {UNICORE_CA_FILE}")
        cafile = UNICORE_CA_FILE

    session = ClientSession(
        connector=TCPConnector(
            ssl=ssl.create_default_context(cafile=cafile),
        ),
    )

    async with session:
        authenticator = Authenticator(session, logger)

        allocator = create_allocator(JOB_ALLOCATOR, session, logger)

        scheduler = JobScheduler(allocator, authenticator, connector, logger)

        cleanup_task = asyncio.create_task(scheduler.cleanup_expired_jobs())

        routes = [
            web.post("/start", scheduler.start),
            web.post("/stop/{job_id:[^{}]+}", scheduler.stop),
            web.get("/status/{job_id:[^{}]+}", scheduler.get_status),
        ]

        try:
            await run_application("VSM", MASTER_PORT, logger, routes)
        finally:
            cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup_task
            await allocator.close()


def run_master() -> None:
    asyncio.run(main())
