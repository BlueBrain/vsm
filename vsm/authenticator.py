from logging import Logger
from http import HTTPStatus

from aiohttp import ClientSession, web

from .settings import KEYCLOAK_HOST, KEYCLOAK_USER_INFO_URL, USE_KEYCLOAK


class Authenticator:
    def __init__(self, session: ClientSession, logger: Logger) -> None:
        self._session = session
        self._logger = logger

    def get_token(self, request: web.Request) -> str:
        self._logger.info("Extracting token from request header")

        token = request.headers.get("Authorization")

        if token is None:
            self._logger.error("No authorization headers")
            raise web.HTTPUnauthorized(text="No authorization header")

        return token

    async def get_username(self, token: str) -> str | None:
        if not USE_KEYCLOAK:
            self._logger.warn("No Keycloak configured, using default user")
            return None

        url = KEYCLOAK_USER_INFO_URL
        headers = {
            "Host": KEYCLOAK_HOST,
            "Authorization": token,
        }

        self._logger.info("Sending Keycloack request")
        self._logger.debug(f"Keycloak request details: {url=} {headers=}")

        try:
            response = await self._session.get(url, headers=headers)
        except Exception as e:
            self._logger.error(f"Adrien's logger saying that KK errors with: {e}")
            raise web.HTTPInternalServerError("KK cert issue")

        status = response.status

        if status != HTTPStatus.OK:
            self._logger.error(f"Keycloak status error (invalid token) {status}")
            raise web.HTTPUnauthorized(text="Invalid Keycloak token")

        self._logger.info("Keycloak status Ok")

        data = await response.json()

        self._logger.debug(f"Keycloak response body: {data}")

        if not isinstance(data, dict):
            self._logger.error("Keycloak response body is not a dict")
            raise web.HTTPInternalServerError(text="Invalid Keycloak response")

        email = data.get("email")

        if email is None or not isinstance(email, str):
            self._logger.error("No valid 'email' key in Keycloak response")
            raise web.HTTPInternalServerError(text="Invalid Keycloak response")

        self._logger.info(f"User ID: {email}")

        return email
