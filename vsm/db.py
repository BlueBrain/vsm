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
    end_time: datetime
    host: str = ""


class DbConnection(Protocol):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def close(self) -> None: ...

    async def recreate_table(self) -> None: ...

    async def get_jobs(self) -> list[Job]: ...

    async def get_job(self, id: str) -> Job | None: ...

    async def insert_job(self, job: Job) -> None: ...

    async def update_job(self, id: str, host: str) -> None: ...

    async def delete_job(self, id: str) -> None: ...


class DbConnector(Protocol):
    async def connect(self) -> DbConnection: ...


TABLE = "jobs"


@dataclass
class Column:
    name: str
    type: str = "VARCHAR(255)"
    primary: bool = False


JOB_ID = "job_id"
HOSTNAME = "hostname"

COLUMNS = [
    Column(JOB_ID, primary=True),
    Column("user_id"),
    Column("start_time"),
    Column("end_time"),
    Column(HOSTNAME),
]


def declare_column(column: Column) -> str:
    suffix = "PRIMARY KEY" if column.primary else "NOT NULL"
    return f"{column.name} {column.type} {suffix}"


def get_all_columns(columns: list[Column]) -> str:
    return ", ".join(column.name for column in columns)


def parse_job(row: dict[str, str]) -> Job:
    return Job(
        id=row[JOB_ID],
        user=row["user_id"],
        start_time=datetime.fromisoformat(row["start_time"]),
        end_time=datetime.fromisoformat(row["end_time"]),
        host=row[HOSTNAME],
    )


def compose_job(job: Job) -> list[str]:
    return [
        job.id,
        job.user,
        job.start_time.isoformat(),
        job.end_time.isoformat(),
        job.host,
    ]


class PsqlConnection(DbConnection):
    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def close(self) -> None:
        await self._connection.close()

    async def recreate_table(self) -> None:
        await self._connection.execute(f"DROP TABLE IF EXISTS {TABLE}")
        columns = ",\n".join(declare_column(column) for column in COLUMNS)
        await self._connection.execute(f"CREATE TABLE {TABLE} (\n{columns}\n)")

    async def get_jobs(self) -> list[Job]:
        columns = get_all_columns(COLUMNS)
        rows = await self._connection.fetch(f"SELECT {columns} FROM {TABLE}")
        return [parse_job(row) for row in rows]

    async def get_job(self, id: str) -> Job | None:
        columns = get_all_columns(COLUMNS)
        query = f"SELECT {columns} FROM {TABLE} WHERE {JOB_ID} = $1"
        row = await self._connection.fetchrow(query, id)
        if row is None:
            return None
        return parse_job(row)

    async def insert_job(self, job: Job) -> None:
        columns = get_all_columns(COLUMNS)
        values = compose_job(job)
        placeholders = ", ".join(f"${i + 1}" for i in range(len(COLUMNS)))
        query = f"INSERT INTO {TABLE}({columns}) VALUES({placeholders})"
        await self._connection.execute(query, *values)

    async def update_job(self, id: str, host: str) -> None:
        query = f"UPDATE {TABLE} SET {HOSTNAME} = $1 WHERE {JOB_ID} = $2"
        await self._connection.execute(query, host, id)

    async def delete_job(self, id: str) -> None:
        query = f"DELETE FROM {TABLE} WHERE {JOB_ID} = $1"
        await self._connection.execute(query, id)


@dataclass
class PsqlConnector(DbConnector):
    host: str
    database: str
    user: str
    password: str

    async def connect(self) -> DbConnection:
        connection = await asyncpg.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password,
        )
        return PsqlConnection(connection)


def create_db_connector() -> DbConnector:
    return PsqlConnector(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD,
    )
