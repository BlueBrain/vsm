import asyncio
from dataclasses import dataclass
from typing import Protocol

import asyncpg

from vsm import settings


@dataclass
class Job:
    id: str
    user: str
    host: str


class DbError(Exception):
    ...


class DbConnector(Protocol):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def close(self) -> None:
        ...

    async def get_job(self, id: str) -> Job:
        ...

    async def insert_job(self, id: str, user: str) -> None:
        ...

    async def update_job(self, id: str, host: str) -> None:
        ...

    async def delete_job(self, id: str) -> None:
        ...


class PsqlConnector(DbConnector):
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def close(self) -> None:
        try:
            await self._connection.close()
        except asyncpg.PostgresError as e:
            raise DbError(str(e))

    async def get_job(self, id: str) -> Job:
        query = """
            SELECT user_id, hostname FROM jobs WHERE job_id = $1
        """
        try:
            row = await self._connection.fetchrow(query, id)
        except asyncpg.PostgresError as e:
            raise DbError(str(e))
        if row is None:
            raise DbError(f"No jobs found with ID {id}")
        return Job(id, row["user_id"], row["hostname"])

    async def insert_job(self, id: str, user: str) -> None:
        query = """
            INSERT INTO jobs(job_id, user_id, hostname) VALUES($1, $2, $3)
        """
        try:
            await self._connection.execute(query, id, user, "")
        except asyncpg.PostgresError as e:
            raise DbError(str(e))

    async def update_job(self, id: str, host: str) -> None:
        query = """
            UPDATE jobs SET hostname = $1 WHERE job_id = $2
        """
        try:
            await self._connection.execute(query, host, id)
        except asyncpg.PostgresError as e:
            raise DbError(str(e))

    async def delete_job(self, id: str) -> None:
        query = """
            DELETE FROM jobs WHERE job_id = $1
        """
        try:
            await self._connection.execute(query, (id))
        except asyncpg.PostgresError as e:
            raise DbError(str(e))


# async def create_table(connection: asyncpg.Connection) -> None:
#     query = """
#         CREATE TABLE IF NOT EXISTS jobs (
#             job_id VARCHAR(255) PRIMARY KEY,
#             user_id VARCHAR(255) NOT NULL,
#             hostname VARCHAR(255) NOT NULL
#         )
#     """
#     await connection.execute(query)

#
# async def drop_table(connection: asyncpg.Connection) -> None:
#     query = """
#         DROP TABLE IF EXISTS jobs
#     """
#     await connection.execute(query)


async def connect() -> DbConnector:
    connection = await asyncpg.connect(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USERNAME,
        password=settings.DB_PASSWORD,
    )
    # await create_table(connection)
    # await drop_table(connection)
    return PsqlConnector(connection)
