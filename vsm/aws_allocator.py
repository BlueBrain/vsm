import uuid
from typing import Any

from .allocator import JobAllocator, JobDetails
from .authenticator import get_username
from .settings import AWS_HOST

END_TIME = "2030-01-01T00:00:00"


class AwsAllocator(JobAllocator):
    async def create_job(self, token: str, payload: dict[str, Any]) -> str:
        await get_username(token)
        return str(uuid.uuid4())

    async def get_job_details(self, token: str, job_id: str) -> JobDetails:
        await get_username(token)
        return JobDetails(job_running=True, end_time=END_TIME, host=AWS_HOST)
