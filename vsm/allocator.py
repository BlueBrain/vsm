from dataclasses import dataclass
from typing import Any, Protocol


class AllocationError(Exception):
    pass


class JobNotFound(Exception):
    pass


@dataclass
class JobDetails:
    job_running: bool = False
    end_time: float | None = None
    host: str | None = None


class JobAllocator(Protocol):
    async def create_job(self, token: str, payload: dict[str, Any]) -> str:
        ...

    async def get_job_details(self, token: str, job_id: str) -> JobDetails:
        ...
