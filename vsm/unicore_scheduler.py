#!/usr/bin/python3
import json
import logging
from json.decoder import JSONDecodeError

from aiohttp import web

from . import auth_helper, db, script_list, settings
from .unicore_handler import UnicoreHandler
from .utils import check_user_owns_job, get_hostname

unicore_handler = UnicoreHandler()


async def _get_stdout(job_id, token):
    working_dir = f"{settings.UNICORE_ENDPOINT}/storages/{job_id}{settings.UNICORE_USPACE_SUFIX}"
    return await unicore_handler.get_file(token, working_dir, "stdout")


class UnicoreScheduler:
    def __init__(self):
        pass

    async def start(self, req):
        try:
            token = req.headers["Authorization"]
            user_id = await auth_helper.get_username(token)
        except (PermissionError, KeyError):
            return web.Response(status=401)

        try:
            body = await req.json()
            usecase = body["usecase"]
            usecase_payload = [e for e in script_list.USE_CASES if e["Name"] == usecase][0]
        except (KeyError, JSONDecodeError, IndexError) as e:
            return web.Response(status=400)

        job_created = await unicore_handler.create_job(token, usecase_payload)

        if job_created.status >= 400:
            logging.error(job_created.content)
            logging.error(f"Unicore returned a {job_created.status} error")
            return web.Response(status=job_created.status)

        if "Location" not in job_created.headers:
            logging.error(f"Unicore response is missing Location header: {job_created.headers}")
            return web.Response(status=500)

        location = job_created.headers["Location"]
        job_id = location.split("/").pop()

        async with await db.connect() as connection:
            await connection.insert_job(job_id, user_id)

        logging.info(f"User {user_id} has created a job: {job_id}")

        return web.Response(status=201, body=json.dumps({"job_id": job_id}))

    async def get_status(self, req):
        try:
            user_id = await auth_helper.get_username(req.headers["Authorization"])
        except PermissionError:
            return web.Response(status=401)

        try:
            job_id = req.match_info["job_id"]
        except KeyError:
            return web.Response(status=400)

        try:
            await check_user_owns_job(job_id, user_id)
        except db.DbError:
            return web.Response(status=404)
        except PermissionError:
            return web.Response(status=403)

        token = req.headers["Authorization"]

        try:
            resp = await unicore_handler.get_job_details(job_id, token)
            end_time = resp["EndTime"]
            job_running = resp["JobState"] == "RUNNING"
            if not job_running:
                return web.Response(
                    status=200,
                    body=json.dumps(
                        {"job_running": False, "end_time": None, "brayns_started": False}
                    ),
                )

        except Exception as e:
            logging.error(e)
            return web.Response(status=500)

        try:
            file_content = await _get_stdout(job_id, token)
            hostname = await get_hostname(file_content)
        except Exception as e:
            logging.warning(f"{job_id} host not ready?")
            return web.Response(
                status=200,
                body=json.dumps(
                    {"job_running": True, "end_time": end_time, "brayns_started": False}
                ),
            )

        async with await db.connect() as connection:
            await connection.update_job(job_id, hostname)

        return web.Response(
            status=200,
            body=json.dumps({f"job_running": True, "end_time": end_time, "brayns_started": True}),
        )
