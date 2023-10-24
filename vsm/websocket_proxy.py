import asyncio
import logging
from typing import cast

from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType, web
from aiohttp.web_request import Request

from . import db

WebSocketLike = ClientWebSocketResponse | web.WebSocketResponse


class WebSocketProxy:
    async def ws_handler(self, request: Request):
        if not self.verify_headers(request):
            return web.HTTPBadRequest(reason="Headers not verified")
        try:
            job_id = request.match_info["job_id"]
            service = request.match_info.get("service")
        except KeyError:
            raise web.HTTPBadRequest()
        except ValueError:
            raise web.HTTPNotFound()
        except PermissionError as e:
            logging.warning(str(e))
            raise web.HTTPUnauthorized(reason=str(e))
        except Exception:
            raise web.HTTPBadRequest()

        try:
            async with await db.connect() as connection:
                job = await connection.get_job(job_id)
        except db.DbError as e:
            logging.warning(e)
            raise web.HTTPNotFound()

        if not job.host:
            logging.warning(f"No host found for job {job_id}")
            raise web.HTTPNotFound()

        hostname = job.host + (":5000" if service == "renderer" else ":8000")

        session = ClientSession()
        ws_client = web.WebSocketResponse(max_msg_size=2 * 1024 * 1024 * 1024)
        try:
            await ws_client.prepare(request)

            async with session.ws_connect(f"ws://{hostname}", max_msg_size=2 * 1024 * 1024 * 1024) as ws_brayns:
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
            await session.close()
            logging.info(f"Client with ip: {request.headers.get('X-FORWARDED-FOR', request.remote)} has left the game")

        return ws_client

    @staticmethod
    def verify_headers(request: Request) -> bool:
        request_headers = request.headers.copy()
        try:
            return (
                request_headers["Connection"].lower() == "keep-alive, upgrade"
                or request_headers["Connection"].lower() == "upgrade"
                and request_headers["Upgrade"].lower() == "websocket"
                and request.method == "GET"
            )
        except Exception:
            return False

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
                    await ws_to.close(code=code, message=msg.extra)
                elif ws_from.closed:
                    logging.error("ws_from is closed")
                else:
                    raise ValueError(f"unexpected message type: {mt}")
        except Exception as e:
            logging.error(f"ws forward exception, {str(e)}")
