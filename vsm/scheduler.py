import asyncio
import json
import logging
from typing import Any

from aiohttp import web

from . import db, script_list
from .allocator import AllocationError, JobAllocator, JobDetails, JobNotFound
from .authenticator import Authenticator

MAX_TASK_DURATION = 8 * 3600


class JobScheduler:
    def __init__(self, allocator: JobAllocator, authenticator: Authenticator):
        self._allocator = allocator
        self._authenticator = authenticator
        self._stop_tasks = dict[str, asyncio.Task]()

    async def start(self, request: web.Request) -> web.Response:
        try:
            token = request.headers["Authorization"]
            user_id = await self._authenticator.get_username(token)
        except KeyError:
            return web.HTTPUnauthorized(body="No authorization header")
        except PermissionError as e:
            return web.HTTPUnauthorized(body=str(e))

        if user_id is None:
            user_id = "SANDBOX_USER"

        try:
            payload = await request.json()
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            return web.HTTPBadRequest(body=str(e))

        try:
            job_id = await self._allocator.create_job(token, payload)
        except AllocationError as e:
            logging.error(f"Allocation failed {e}")
            return web.HTTPInternalServerError(body="Job allocation failed")

        async with await db.connect() as connection:
            await connection.insert_job(job_id, user_id)

        logging.info(f"User {user_id} has created a job: {job_id}")

        stop = self._stop_after(token, job_id, MAX_TASK_DURATION)
        self._stop_tasks[job_id] = asyncio.create_task(stop)

        return web.HTTPCreated(body=json.dumps({"job_id": job_id}))

    async def stop(self, request: web.Request) -> web.Response:
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

        try:
            await _check_user_owns_job(job_id, user_id)
        except db.DbError as e:
            logging.error(f"DB error to check user owns job {e}")
            return web.HTTPNotFound(body=str(e))
        except PermissionError as e:
            return web.HTTPForbidden(body=str(e))

        try:
            await self._stop(token, job_id)
        except JobNotFound as e:
            logging.error(e)
            return web.HTTPBadRequest(body=str(e))
        except Exception as e:
            logging.error(e)
            return web.HTTPInternalServerError()

        return web.HTTPOk()

    async def get_status(self, request: web.Request) -> web.Response:
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

        try:
            await _check_user_owns_job(job_id, user_id)
        except db.DbError as e:
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

        if details.host is None:
            return _reply(details)

        async with await db.connect() as connection:
            await connection.update_job(job_id, details.host)

        return _reply(details)

    async def _stop_after(self, token: str, job_id: str, delay: float) -> None:
        await asyncio.sleep(delay)
        try:
            await self._stop(token, job_id)
        except Exception as e:
            logging.error(f"Failed to execute scheduled stop: {e}")

    async def _stop(self, token: str, job_id: str) -> None:
        await self._allocator.destroy_job(token, job_id)

        async with await db.connect() as connection:
            await connection.delete_job(job_id)

        try:
            self._stop_tasks[job_id].cancel()
            del self._stop_tasks[job_id]
        except KeyError:
            raise JobNotFound(f"Job not found {job_id}")


async def _check_user_owns_job(job_id: str, user_id: str | None) -> None:
    if user_id is None:
        return
    async with await db.connect() as connection:
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
