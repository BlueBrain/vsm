import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from aiohttp import web

from .allocator import AllocationError, JobAllocator, JobDetails, JobNotFound
from .authenticator import Authenticator
from .db import DbError, Job, connect_to_db

CLEANUP_PERIOD = timedelta(seconds=10)
MAX_TASK_DURATION = timedelta(hours=8)


class JobScheduler:
    def __init__(self, allocator: JobAllocator, authenticator: Authenticator):
        self._allocator = allocator
        self._authenticator = authenticator

    async def start(self, request: web.Request) -> web.Response:
        logging.info("New start request.")

        try:
            token = request.headers["Authorization"]
            user_id = await self._authenticator.get_username(token)
        except KeyError:
            return web.HTTPUnauthorized(body="No authorization header")
        except PermissionError as e:
            return web.HTTPUnauthorized(body=str(e))

        if user_id is None:
            logging.info("Using sandbox user")
            user_id = "SANDBOX_USER"

        try:
            payload = await request.json()
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            return web.HTTPBadRequest(body=str(e))

        logging.info(f"Request body {payload}")

        try:
            job_id = await self._allocator.create_job(token, payload)
        except AllocationError as e:
            logging.error(f"Allocation failed {e}")
            return web.HTTPInternalServerError(body="Job allocation failed")

        logging.info(f"User {user_id} has created a job: {job_id}")

        start_time = datetime.now()
        job = Job(job_id, user_id, start_time)

        async with await connect_to_db() as connection:
            await connection.insert_job(job)

        logging.info("Job saved to DB")

        return web.HTTPCreated(body=json.dumps({"job_id": job_id}))

    async def stop(self, request: web.Request) -> web.Response:
        logging.info("New stop request.")

        try:
            token = request.headers["Authorization"]
            user_id = await self._authenticator.get_username(token)
        except PermissionError as e:
            return web.HTTPUnauthorized(body=str(e))
        except KeyError:
            return web.HTTPBadRequest(body="No authorization header")

        try:
            job_id = request.match_info["job_id"]
        except KeyError:
            return web.HTTPBadRequest(body="No job_id provided")

        logging.info(f"Job ID to stop {job_id}")

        try:
            await _check_user_owns_job(job_id, user_id)
        except DbError as e:
            logging.error(f"DB error to check user owns job {e}")
            return web.HTTPNotFound(body=str(e))
        except PermissionError as e:
            return web.HTTPForbidden(body=str(e))

        try:
            await self._kill_job(job_id)
        except JobNotFound as e:
            return web.HTTPBadRequest(body=str(e))
        except Exception as e:
            return web.HTTPInternalServerError(body=str(e))

        return web.HTTPOk()

    async def get_status(self, request: web.Request) -> web.Response:
        logging.info("New status request.")

        try:
            token = request.headers["Authorization"]
            user_id = await self._authenticator.get_username(token)
        except PermissionError as e:
            return web.HTTPUnauthorized(body=str(e))
        except KeyError:
            return web.HTTPBadRequest(body="No authorization header")

        try:
            job_id = request.match_info["job_id"]
        except KeyError:
            return web.HTTPBadRequest(body="No job_id provided")

        logging.info(f"Job ID to get status {job_id}")

        try:
            await _check_user_owns_job(job_id, user_id)
        except DbError as e:
            logging.error(f"DB error to check user owns job {e}")
            return web.HTTPNotFound(body=str(e))
        except PermissionError as e:
            return web.HTTPForbidden(body=str(e))

        try:
            details = await self._allocator.get_job_details(token, job_id)
        except JobNotFound as e:
            logging.error(e)
            return web.HTTPBadRequest(body=str(e))
        except Exception as e:
            logging.error(e)
            return web.HTTPInternalServerError()

        logging.info(f"Job details from allocator {details}")

        if details.host is None:
            return _reply(details)

        async with await connect_to_db() as connection:
            await connection.update_job(job_id, details.host)

        logging.info("Updated job host in DB")

        return _reply(details)

    async def cleanup_expired_jobs(self) -> None:
        while True:
            await asyncio.sleep(CLEANUP_PERIOD.total_seconds())

            async with await connect_to_db() as connection:
                jobs = await connection.get_jobs()

            now = datetime.now()
            for job in jobs:
                if now - job.start_time >= MAX_TASK_DURATION:
                    await self._kill_job(job.id)

    async def _kill_job(self, job_id: str) -> None:
        logging.info(f"Stopping job {job_id}")

        await self._allocator.destroy_job(job_id)

        logging.info(f"Removing job {job_id} from DB")

        async with await connect_to_db() as connection:
            await connection.delete_job(job_id)


async def _check_user_owns_job(job_id: str, user_id: str | None) -> None:
    if user_id is None:
        return
    async with await connect_to_db() as connection:
        job = await connection.get_job(job_id)
        if job.user != user_id:
            logging.warning(f"Job creator {job.user} doesn't match keycloak username {user_id}")
            raise PermissionError(f"{job.user} is not the owner of the job {job_id}")


def _serialize_details(details: JobDetails) -> dict[str, Any]:
    return {
        "job_running": details.job_running,
        "end_time": details.end_time,
        "brayns_started": details.host is not None,
    }


def _reply(details: JobDetails) -> web.Response:
    message = _serialize_details(details)
    return web.HTTPOk(body=json.dumps(message))
