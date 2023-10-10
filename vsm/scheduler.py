import json
import logging
from typing import Any

from aiohttp import web

from . import authenticator, db, script_list
from .allocator import AllocationError, JobAllocator, JobDetails, JobNotFound


class JobScheduler:
    def __init__(self, allocator: JobAllocator):
        self._allocator = allocator

    async def start(self, request: web.Request):
        try:
            token = request.headers["Authorization"]
            user_id = await authenticator.get_username(token)
        except (PermissionError, KeyError):
            return web.Response(status=401)

        try:
            body = await request.json()
            usecase = body["usecase"]
            usecase_payload = [e for e in script_list.USE_CASES if e["Name"] == usecase][0]
        except (KeyError, json.JSONDecodeError, IndexError):
            return web.Response(status=400)

        try:
            job_id = await self._allocator.create_job(token, usecase_payload)
        except AllocationError:
            return web.Response(status=500)

        async with await db.connect() as connection:
            await connection.insert_job(job_id, user_id)

        logging.info(f"User {user_id} has created a job: {job_id}")

        return web.Response(status=201, body=json.dumps({"job_id": job_id}))

    async def get_status(self, request: web.Request):
        try:
            user_id = await authenticator.get_username(request.headers["Authorization"])
        except PermissionError:
            return web.Response(status=401)

        try:
            job_id = request.match_info["job_id"]
        except KeyError:
            return web.Response(status=400)

        try:
            await _check_user_owns_job(job_id, user_id)
        except db.DbError:
            return web.Response(status=404)
        except PermissionError:
            return web.Response(status=403)

        token = request.headers["Authorization"]

        try:
            details = await self._allocator.get_job_details(token, job_id)
        except JobNotFound as e:
            logging.error(e)
            return web.Response(status=400)
        except Exception as e:
            logging.error(e)
            return web.Response(status=500)

        if details.host is None:
            return _reply(details)

        async with await db.connect() as connection:
            await connection.update_job(job_id, details.host)

        return _reply(details)


async def _check_user_owns_job(job_id, user_id):
    async with await db.connect() as connection:
        job = await connection.get_job(job_id)
        if job.user != user_id:
            logging.warning(f"Job creator {job.user} doesn't match keycloak username {user_id}")
            raise PermissionError


def _serialize_details(details: JobDetails) -> dict[str, Any]:
    return {
        "job_running": details.job_running,
        "end_time": details.end_time,
        "brayns_started": details.host is not None,
    }


def _reply(details: JobDetails) -> web.Response:
    message = _serialize_details(details)
    return web.Response(status=200, body=json.dumps(message))
