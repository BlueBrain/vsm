import logging
from http import HTTPStatus

import aiohttp

from .settings import BBP_KEYCLOAK_HOST, BBP_KEYCLOAK_USER_INFO_URL


async def get_username(token: str):
    url = BBP_KEYCLOAK_USER_INFO_URL

    request_headers = {
        "Host": BBP_KEYCLOAK_HOST,
        "Authorization": token,
    }

    logging.debug(f"Request headers to `{url}`: {request_headers}")

    async with aiohttp.ClientSession() as session:
        client_response = await session.get(url, headers=request_headers)

        if client_response.status == HTTPStatus.OK:
            return (await client_response.json())["email"]
        else:
            raise PermissionError("Token issue")
