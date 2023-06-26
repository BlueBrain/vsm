import logging

import aiohttp
# TODO move to settings/config
BBP_KEYCLOAK_USER_INFO_URL = (
    "https://bbpauth.epfl.ch/auth/realms/BBP/protocol/openid-connect/userinfo"
)
BBP_KEYCLOAK_HOST = "bbpauth.epfl.ch"


async def get_username(token: str):
    url = BBP_KEYCLOAK_USER_INFO_URL

    request_headers = {
        "Host": BBP_KEYCLOAK_HOST,
        "Authorization": token,
    }
    logging.debug(f"Request headers to `{url}`: {request_headers}")
    async with aiohttp.ClientSession() as session:
        client_response = await session.get(url, headers=request_headers)
        from http import HTTPStatus

        if client_response.status == HTTPStatus.OK:
            return (await client_response.json())["email"]
        else:
            raise PermissionError("Token issue")
