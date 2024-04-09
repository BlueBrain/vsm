from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import asyncpg

from .settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_USERNAME


@dataclass
class Job:
    id: str
    user: str
    start_time: datetime
    host: str = ""


class DbError(Exception): ...


class DbConnection(Protocol):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def close(self) -> None: ...

    async def create_table_if_not_exists(self) -> None: ...

    async def get_jobs(self) -> list[Job]: ...

    async def get_job(self, id: str) -> Job: ...

    async def insert_job(self, job: Job) -> None: ...

    async def update_job(self, id: str, host: str) -> None: ...

    async def delete_job(self, id: str) -> None: ...


class PsqlConnection(DbConnection):
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def close(self) -> None:
        try:
            await self._connection.close()
        except asyncpg.PostgresError as e:
            raise DbError(str(e))

    async def create_table_if_not_exists(self) -> None:
        query = """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id VARCHAR(255) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                start_time VARCHAR(255) NOT NULL
                hostname VARCHAR(255) NOT NULL
            )
        """
        try:
            await self._connection.execute(query)
        except asyncpg.PostgresError as e:
            raise DbError(str(e))

    async def get_jobs(self) -> list[Job]:
        query = """
            SELECT job_id, user_id, start_time, hostname FROM jobs
        """
        try:
            rows = await self._connection.fetch(query)
        except asyncpg.PostgresError as e:
            raise DbError(str(e))
        return [_get_job(row) for row in rows]

    async def get_job(self, id: str) -> Job:
        query = """
            SELECT job_id, user_id, start_time, hostname FROM jobs WHERE job_id = $1
        """
        try:
            row = await self._connection.fetchrow(query, id)
        except asyncpg.PostgresError as e:
            raise DbError(str(e))
        if row is None:
            raise DbError(f"No jobs found with ID {id}")
        return _get_job(row)

    async def insert_job(self, job: Job) -> None:
        query = """
            INSERT INTO jobs(job_id, user_id, start_time, hostname) VALUES($1, $2, $3, $4)
        """
        start_time = job.start_time.isoformat()
        try:
            await self._connection.execute(query, job.id, job.user, start_time, job.host)
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
            await self._connection.execute(query, id)
        except asyncpg.PostgresError as e:
            raise DbError(str(e))


async def connect_to_db() -> DbConnection:
    connection = await asyncpg.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD,
    )
    return PsqlConnection(connection)


def _get_job(row: dict[str, str]) -> Job:
    return Job(
        id=row["job_id"],
        user=row["user_id"],
        start_time=datetime.fromisoformat(row["start_time"]),
        host=row["hostname"],
    )
