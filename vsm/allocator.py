import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from .logger import Logger


@dataclass
class JobDetails:
    end_time: datetime | None = None
    host: str | None = None

    @property
    def ready(self) -> bool:
        return self.host is not None


class JobAllocator(Protocol):
    async def close(self) -> None: ...

    async def create_job(self, token: str, payload: dict[str, Any]) -> str: ...

    async def destroy_job(self, job_id: str) -> None: ...

    async def get_job_details(self, token: str, job_id: str) -> JobDetails: ...


class FakeAllocator(JobAllocator):
    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def close(self) -> None:
        self._logger.info("Allocator closed")

    async def create_job(self, token: str, payload: dict[str, Any]) -> str:
        self._logger.info(f"Create job {token=} {payload=}")
        return uuid.uuid4().hex

    async def destroy_job(self, job_id: str) -> None:
        self._logger.info(f"Destroy job {job_id}")

    async def get_job_details(self, token: str, job_id: str) -> JobDetails:
        self._logger.info(f"Get job details {token=} {job_id=}")
        return JobDetails(host="localhost")
