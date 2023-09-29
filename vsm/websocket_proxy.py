#!/usr/bin/python3
import asyncio
import logging
import pprint

from aiohttp import ClientSession, WSMsgType, web
from aiohttp.web_request import Request

from . import db


class WebSocketProxy:
    async def ws_handler(self, req: Request):
        """
        ---
        parameters:
        - in: query
          name: job_id
          schema:
            type: string
          required: true
          description: |
            Job id I gues
          example:
            213
        - in: path
          name: channel_name
          schema:
            enum:
             - "RENDERER"
             - "BACKEND"
          required: true
          description: |
            Channel type to distingush if a connectgions is meant for backend or renderer
          example:
            backend
        responses:
            "200":
                 description: successful operation.
            "404":
                description: job_id might not be valid
            "400":
                description: WS negotiation failed
        """

        if not self.verify_headers(req):
            return web.HTTPBadRequest(reason="Headers not verified")
        try:
            job_id = req.match_info["job_id"]
            service = req.match_info.get("service")
        except KeyError as e:
            raise web.HTTPBadRequest()
        except ValueError as e:
            raise web.HTTPNotFound()
        except PermissionError as e:
            logging.warning(str(e))
            raise web.HTTPUnauthorized(reason=str(e))
        except Exception as e:
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
        session = None
        try:
            session = ClientSession()
            ws_client = web.WebSocketResponse(max_msg_size=2*1024*1024*1024)
            await ws_client.prepare(req)
            async with session.ws_connect(f"ws://{hostname}", max_msg_size=2*1024*1024*1024) as ws_brayns:
                try:
                    logging.info(f"Hurray, a new client with ip {req.headers.get('X-FORWARDED-FOR', req.remote)}")
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
            logging.info(f"Client with ip: {req.headers.get('X-FORWARDED-FOR', req.remote)} has left the game")

        return ws_client

    @staticmethod
    def verify_headers(req):
        request_headers = req.headers.copy()
        try:
            return (
                request_headers["Connection"].lower() == "keep-alive, upgrade"
                or request_headers["Connection"].lower() == "upgrade"
                and request_headers["Upgrade"].lower() == "websocket"
                and req.method == "GET"
            )
        except:
            return False

    async def wsforward(self, ws_from, ws_to):
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
                    await ws_to.close(code=ws_to.close_code, message=msg.extra)
                elif ws_from.closed:
                    logging.error("ws_from is closed")
                else:
                    raise ValueError(
                        "unexpected message type: %s",
                        pprint.pformat(msg),
                    )
        except Exception as e:
            logging.error(f"ws forward exception, {str(e)}")
