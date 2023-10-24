import logging
from http import HTTPStatus

from aiohttp import ClientSession

from .settings import KEYCLOAK_HOST, KEYCLOAK_USER_INFO_URL


async def get_username(token: str):
    url = KEYCLOAK_USER_INFO_URL

    headers = {
        "Host": KEYCLOAK_HOST,
        "Authorization": token,
    }

    logging.debug(f"Request headers to `{url}`: {headers}")

    async with ClientSession() as session:
        response = await session.get(url, headers=headers)

        if response.status != HTTPStatus.OK:
            raise PermissionError("Token issue")

        data = await response.json()

        return data["email"]
