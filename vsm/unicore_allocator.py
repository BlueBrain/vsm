import logging
import re
from typing import Any

from aiohttp import ClientSession

from . import script_list
from .allocator import AllocationError, JobAllocator, JobDetails, JobNotFound
from .settings import UNICORE_ENDPOINT


class UnicoreAllocator(JobAllocator):
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def create_job(self, token: str, payload: dict[str, Any]) -> str:
        url = f"{UNICORE_ENDPOINT}/jobs"
        headers = _get_json_headers(token)
        usecase = payload["usecase"]
        usecase_payload = next(e for e in script_list.USE_CASES if e["Name"] == usecase)

        async with self._session.post(url, json=usecase_payload, headers=headers) as response:
            if response.status >= 400:
                logging.error(response.content)
                logging.error(f"Unicore returned a {response.status} error")
                raise AllocationError("Request to Unicore failed")

            location = response.headers.get("Location")

            if location is None:
                logging.error("Unicore response is missing 'Location' header")
                raise AllocationError("Invalid Unicore response")

            return location.split("/").pop()

    async def destroy_job(self, job_id: str) -> None:
        raise NotImplementedError("Not available for unicore")

    async def get_job_details(self, token: str, job_id: str) -> JobDetails:
        url = f"{UNICORE_ENDPOINT}/jobs/{job_id}/details"
        headers = _get_json_headers(token)

        try:
            async with self._session.get(url, headers=headers) as response:
                data = await response.json()
        except Exception as e:
            logging.error(f"Unicore status check failed: {e}")
            raise JobNotFound(job_id)

        job_state = data.get("JobState")
        if job_state is None:
            return JobDetails()

        running = bool(job_state == "RUNNING")

        if not running:
            return JobDetails()

        end_time = data["EndTime"]

        try:
            content = await self._get_stdout(token, job_id)
        except Exception:
            logging.debug("Host not ready ?")
            return JobDetails(job_running=True, end_time=end_time)

        host = _get_hostname(content.decode())

        return JobDetails(job_running=True, end_time=end_time, host=host)

    async def _get_stdout(self, token: str, job_id: str) -> bytes:
        storage = f"{UNICORE_ENDPOINT}/storages/{job_id}-uspace"
        url = f"{storage}/files/stdout"
        headers = _get_stream_headers(token)

        async with self._session.get(url, headers=headers) as response:
            if response.status == 404:
                raise JobNotFound(job_id)
            return await response.read()


def _get_json_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"{token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _get_stream_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"{token}", "Accept": "application/octet-stream"}


def _get_hostname(content: str) -> str | None:
    if "HOSTNAME" not in content:
        return None
    return re.findall("\\w*.bbp.epfl.ch", content)[0]
