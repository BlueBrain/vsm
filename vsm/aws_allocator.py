from typing import Any

from .allocator import JobAllocator, JobDetails, JobNotFound
from .authenticator import get_username
from .settings import AWS_HOST

AWS_JOB_ID = "aws_fixed_job_id"


class AwsAllocator(JobAllocator):
    async def create_job(self, token: str, _: dict[str, Any]) -> str:
        await get_username(token)
        return AWS_JOB_ID

    async def get_job_details(self, token: str, job_id: str) -> JobDetails:
        await get_username(token)
        if job_id != AWS_JOB_ID:
            raise JobNotFound(job_id)
        return JobDetails(job_running=True, end_time=100000000000, host=AWS_HOST)
