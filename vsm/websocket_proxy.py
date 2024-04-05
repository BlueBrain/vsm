import asyncio
import logging
from typing import cast

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType, web
from aiohttp.web_request import Request

from vsm.settings import BCSB_PORT, BRAYNS_PORT

from . import db

WebSocketLike = ClientWebSocketResponse | web.WebSocketResponse


class WebSocketProxy:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def ws_handler(self, request: Request):
        if not _verify_headers(request):
            return web.HTTPBadRequest(reason="Headers not verified")

        try:
            job_id = request.match_info["job_id"]
            service = request.match_info.get("service")
        except KeyError as e:
            return web.HTTPBadRequest(body=str(e))
        except ValueError as e:
            return web.HTTPNotFound(body=str(e))
        except PermissionError as e:
            return web.HTTPUnauthorized(body=str(e))
        except Exception:
            return web.HTTPInternalServerError()

        try:
            async with await db.connect() as connection:
                job = await connection.get_job(job_id)
        except db.DbError as e:
            logging.warning(e)
            return web.HTTPNotFound(body=str(e))

        if not job.host:
            logging.warning(f"No host found for job {job_id}")
            return web.HTTPNotFound(body=f"No host found for job {job_id}")

        hostname = job.host + (f":{BRAYNS_PORT}" if service == "renderer" else f":{BCSB_PORT}")

        ws_client = web.WebSocketResponse(max_msg_size=2 * 1024 * 1024 * 1024)
        try:
            await ws_client.prepare(request)

            async with self._session.ws_connect(f"ws://{hostname}", max_msg_size=2 * 1024 * 1024 * 1024) as ws_brayns:
                try:
                    logging.info(
                        f"Hurray, a new client with ip {request.headers.get('X-FORWARDED-FOR', request.remote)}"
                    )
                    task1 = asyncio.create_task(self.wsforward(ws_brayns, ws_client))
                    task2 = asyncio.create_task(self.wsforward(ws_client, ws_brayns))
                    await asyncio.wait([task1, task2], return_when=asyncio.FIRST_COMPLETED)
                except Exception as e:
                    await ws_brayns.close()
                    raise Exception(f"Client or server exception in WS processing: {str(e)}")
        except Exception as e:
            logging.error(f"Error on establishing WS: {str(e)}")
        finally:
            logging.info(f"Client with ip: {request.headers.get('X-FORWARDED-FOR', request.remote)} has left the game")

        return ws_client

    async def wsforward(self, ws_from: WebSocketLike, ws_to: WebSocketLike) -> None:
        try:
            async for msg in ws_from:
                mt = msg.type
                md = msg.data
                if mt == WSMsgType.TEXT:
                    await ws_to.send_str(md)
                elif mt == WSMsgType.BINARY:
                    await ws_to.send_bytes(md)
                elif mt == WSMsgType.CLOSED:
                    logging.error("WSMsgType is closed")
                elif ws_to.closed:
                    logging.error("ws_to is closed")
                    code = cast(int, ws_to.close_code)
                    await ws_to.close(code=code)
                elif ws_from.closed:
                    logging.error("ws_from is closed")
                else:
                    raise ValueError(f"unexpected message type: {mt}")
        except Exception as e:
            logging.error(f"ws forward exception, {str(e)}")


def _verify_headers(request: Request) -> bool:
    request_headers = request.headers
    try:
        return (
            request_headers["Connection"].lower() == "keep-alive, upgrade"
            or request_headers["Connection"].lower() == "upgrade"
            and request_headers["Upgrade"].lower() == "websocket"
            and request.method == "GET"
        )
    except Exception:
        return False
