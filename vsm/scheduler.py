import asyncio
import json
from datetime import datetime, timedelta
from logging import Logger

from aiohttp import web

from .allocator import JobAllocator, JobDetails
from .authenticator import Authenticator
from .db import DbConnector, Job
from .settings import JOB_CLEANUP_PERIOD_SECONDS, JOB_DURATION_SECONDS, PROXY_URL

CLEANUP_PERIOD = timedelta(seconds=JOB_CLEANUP_PERIOD_SECONDS)
JOB_DURATION = timedelta(seconds=JOB_DURATION_SECONDS)


class JobScheduler:
    def __init__(
        self,
        allocator: JobAllocator,
        authenticator: Authenticator,
        connector: DbConnector,
        logger: Logger,
    ) -> None:
        self._allocator = allocator
        self._authenticator = authenticator
        self._connector = connector
        self._logger = logger

    async def start(self, request: web.Request) -> web.Response:
        self._logger.info("Start request received")

        token = self._authenticator.get_token(request)
        user_id = await self._authenticator.get_username(token)

        if user_id is None:
            self._logger.warn("Using sandbox user for DB")
            user_id = "SANDBOX_USER"

        self._logger.info("Extracting JSON body")

        try:
            payload = await request.json()
        except json.JSONDecodeError as e:
            self._logger.error(f"Invalid JSON in user request body {e=}")
            raise web.HTTPBadRequest(text=f"Invalid JSON body: {e}")

        self._logger.debug(f"Request body {payload}")

        job_id = await self._allocator.create_job(token, payload)

        start_time = datetime.now()
        end_time = start_time + JOB_DURATION

        job = Job(job_id, user_id, start_time, end_time)

        self._logger.debug(f"Job details: {job}")

        self._logger.info("Saving new job to DB")

        try:
            async with await self._connector.connect() as connection:
                await connection.insert_job(job)
        except Exception as e:
            self._logger.critical(f"Failed to save job to DB: {e}")
            raise web.HTTPInternalServerError(text="Internal DB error (job is started but not registered)")

        self._logger.info("Job saved to DB")

        return web.HTTPCreated(text=json.dumps({"job_id": job_id}))

    async def stop(self, request: web.Request) -> web.Response:
        self._logger.info("Stop request received")

        token = self._authenticator.get_token(request)
        user_id = await self._authenticator.get_username(token)

        job_id = self._get_job_id_from_path(request)

        self._logger.info(f"Job ID to stop {job_id}")

        job = await self._get_job_from_db(job_id)

        await self._check_user_owns_job(job, user_id)

        await self._kill_job(job_id)

        return web.HTTPOk()

    async def get_status(self, request: web.Request) -> web.Response:
        self._logger.info("Status request received")

        token = self._authenticator.get_token(request)
        user_id = await self._authenticator.get_username(token)

        job_id = self._get_job_id_from_path(request)

        self._logger.info(f"Job ID to get status {job_id}")

        job = await self._get_job_from_db(job_id)

        await self._check_user_owns_job(job, user_id)

        details = await self._allocator.get_job_details(token, job_id)

        if details.end_time is None:
            self._logger.info("Using endtime from DB as allocator did not provide it")
            details.end_time = job.end_time

        self._logger.info(f"Job details: {details}")

        if details.host is None:
            return _serialize_response(job_id, details)

        try:
            async with await self._connector.connect() as connection:
                await connection.update_job(job_id, details.host)
        except Exception as e:
            self._logger.critical(f"DB error while updating jobs: {e}")
            raise web.HTTPInternalServerError(text="Internal DB error (job host is not updated)")

        self._logger.info("Updated job host in DB")

        return _serialize_response(job_id, details)

    async def cleanup_expired_jobs(self) -> None:
        while True:
            await asyncio.sleep(CLEANUP_PERIOD.total_seconds())

            try:
                async with await self._connector.connect() as connection:
                    jobs = await connection.get_jobs()
            except Exception as e:
                self._logger.critical(f"DB error while cleaning jobs: {e}")

            now = datetime.now()

            for job in jobs:
                if now < job.end_time:
                    continue

                try:
                    await self._kill_job(job.id)
                except Exception as e:
                    self._logger.critical(f"Failed to cleanup job {job.id}: {e}")

    async def _kill_job(self, job_id: str) -> None:
        self._logger.info(f"Stopping job {job_id}")

        await self._allocator.destroy_job(job_id)

        self._logger.info(f"Removing job {job_id} from DB")

        try:
            async with await self._connector.connect() as connection:
                await connection.delete_job(job_id)
        except Exception as e:
            self._logger.critical(f"Failed to delete job {job_id} from DB: {e}")
            raise web.HTTPInternalServerError(text="Internal DB error (but job is stopped)")

    async def _get_job_from_db(self, job_id: str) -> Job:
        try:
            async with await self._connector.connect() as connection:
                job = await connection.get_job(job_id)
        except Exception as e:
            self._logger.error(f"DB error while getting job: {e}")
            raise web.HTTPInternalServerError(text="Internal DB error (cannot retreive job)")

        if job is None:
            self._logger.error(f"Job not found for ID {job_id}")
            raise web.HTTPNotFound(text=f"Invalid job ID {job_id}")

        return job

    async def _check_user_owns_job(self, job: Job, user_id: str | None) -> None:
        self._logger.info(f"Checking that user {user_id} owns job {job.id}")

        if user_id is None:
            return

        if job.user != user_id:
            self._logger.error(f"User {user_id} cannot delete job from user {job.user}")
            raise web.HTTPUnauthorized(text="Cannot delete the jobs from another user")

    def _get_job_id_from_path(self, request: web.Request) -> str:
        self._logger.info("Getting job ID from request path")

        job_id = request.match_info.get("job_id")

        if job_id is None:
            self._logger.error("No job ID provided by user")
            raise web.HTTPBadRequest(text="No job_id provided in path")

        return job_id


def _serialize_response(job_id: str, details: JobDetails) -> web.Response:
    assert details.end_time is not None

    message = {
        "ready": details.ready,
        "end_time": details.end_time.isoformat(),
    }

    if details.ready:
        message["job_url"] = f"{PROXY_URL}/{job_id}/renderer"

    return web.HTTPOk(text=json.dumps(message))
