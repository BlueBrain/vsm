from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


JOB_ID = "job_id"
USER_ID = "user_id"
START_TIME = "start_time"
END_TIME = "end_time"
HOSTNAME = "hostname"


@dataclass
class Job:
    id: str
    user: str
    start_time: datetime
    end_time: datetime
    host: str = ""


def parse_job(row: dict[str, str]) -> Job:
    return Job(
        id=row[JOB_ID],
        user=row[USER_ID],
        start_time=datetime.fromisoformat(row[START_TIME]),
        end_time=datetime.fromisoformat(row[END_TIME]),
        host=row[HOSTNAME],
    )


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

