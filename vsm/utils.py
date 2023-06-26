import json
import logging
import re

import aiohttp_cors
from aiohttp import web

from . import db


async def get_hostname(file_content):
    if b"HOSTNAME" not in file_content:
        raise ValueError("HOSTNAME missing")
    return re.findall("\\w*.bbp.epfl.ch", file_content.decode())[0]


async def check_user_owns_job(job_id, user_id):
    async with await db.connect() as connection:
        job = await connection.get_job(job_id)
        if job.user != user_id:
            logging.warning(f"Job creator {job.user} doesn't match keycloak username {user_id}")
            raise PermissionError


def setup_cors(app):
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods="*"
            )
        },
    )
    # Configure CORS on all routes (including method OPTIONS)
    for route in list(app.router.routes()):
        cors.add(route)
