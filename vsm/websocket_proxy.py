import asyncio
from logging import Logger

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType, web
from aiohttp.web_request import Request

from .db import DbConnector
from .settings import BRAYNS_PORT

MAX_MESSAGE_SIZE = 2 * 1024 * 1024 * 1024

WebSocketLike = ClientWebSocketResponse | web.WebSocketResponse


class WebSocketProxy:
    def __init__(self, session: ClientSession, connector: DbConnector, logger: Logger) -> None:
        self._session = session
        self._connector = connector
        self._logger = logger

    async def ws_handler(self, request: Request):
        self._logger.info(f"New websocket connection from {request.host}")

        job_id = request.match_info.get("job_id")

        if job_id is None:
            self._logger.error(f"No job ID in path: {request.path}")
            raise web.HTTPBadRequest(text="No job ID in path")

        try:
            async with await self._connector.connect() as connection:
                job = await connection.get_job(job_id)
        except Exception as e:
            self._logger.error(f"DB error while getting job details: {e}")
            return web.HTTPInternalServerError(text="Internal DB error (cannot retreive job)")

        if job is None:
            self._logger.error(f"Invalid job ID from user: {job_id}")
            raise web.HTTPNotFound(text=f"No jobs found with ID {job_id}")

        if not job.host:
            self._logger.error(f"No host found for job {job_id}")
            return web.HTTPBadRequest(text="Job not ready")

        hostname = f"{job.host}:{BRAYNS_PORT}"

        self._logger.info(f"Brayns hostname: {hostname}")

        ws_client = web.WebSocketResponse(max_msg_size=MAX_MESSAGE_SIZE)

        await ws_client.prepare(request)

        try:
            async with self._session.ws_connect(f"ws://{hostname}", max_msg_size=MAX_MESSAGE_SIZE) as ws_brayns:
                self._logger.info("Websocket session started")
                task1 = asyncio.create_task(self.wsforward("brayns", ws_brayns, ws_client))
                task2 = asyncio.create_task(self.wsforward("client", ws_client, ws_brayns))
                await asyncio.wait([task1, task2], return_when=asyncio.FIRST_COMPLETED)
        except Exception as e:
            self._logger.error(f"WS forward error: {e}")
            raise web.HTTPInternalServerError(text="WS proxy error")

        self._logger.info(f"Client with ip {request.host} disconnected")

        return ws_client

    async def wsforward(self, source: str, ws_from: WebSocketLike, ws_to: WebSocketLike) -> None:
        async for message in ws_from:
            message_type = message.type

            self._logger.info(f"WS message received from {source} {message_type=}")

            if message_type == WSMsgType.TEXT:
                await ws_to.send_str(message.data)
                continue

            if message_type == WSMsgType.BINARY:
                await ws_to.send_bytes(message.data)
                continue

            if message_type == WSMsgType.PING:
                await ws_to.ping()
                continue

            if message_type == WSMsgType.PONG:
                await ws_to.pong()
                continue

            self._logger.error(f"Invalid WS message type {message_type}")
            raise ValueError("Invalid websocket message type")

        await ws_to.close()
