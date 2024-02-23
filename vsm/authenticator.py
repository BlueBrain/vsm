import logging
from http import HTTPStatus

from aiohttp import ClientSession

from .settings import KEYCLOAK_HOST, KEYCLOAK_USER_INFO_URL, USE_KEYCLOAK


class Authenticator:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def get_username(self, token: str) -> str | None:
        if not USE_KEYCLOAK:
            return None

        url = KEYCLOAK_USER_INFO_URL
        headers = {
            "Host": KEYCLOAK_HOST,
            "Authorization": token,
        }

        logging.debug(f"Keycloak request: `{url=}`: {headers=}")

        response = await self._session.get(url, headers=headers)

        logging.debug(f"Keycloak response status code: {response.status}")

        if response.status != HTTPStatus.OK:
            raise PermissionError("Invalid Keycloak token")

        data = await response.json()

        logging.debug(f"Keycloak response body: {data}")

        if not isinstance(data, dict):
            raise ValueError("Invalid Keycloak response")

        email = data.get("email")

        if email is None:
            raise ValueError("No email in Keycloak response")

        return email
