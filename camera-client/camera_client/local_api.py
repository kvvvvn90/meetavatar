"""Local HTTP API server for web-to-desktop communication.

Runs an aiohttp server on port 18520 in a background daemon thread.
The web frontend calls these endpoints to detect the desktop app
and push avatars into it.
"""

import asyncio
import json
import logging
import queue
import threading

from aiohttp import web

logger = logging.getLogger(__name__)

# Allowed CORS origins (Vite dev + Node dev)
_ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
}


def _cors_headers(request: web.Request) -> dict[str, str]:
    origin = request.headers.get("Origin", "")
    if origin in _ALLOWED_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    return {}


@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        return web.Response(status=204, headers=_cors_headers(request))
    resp = await handler(request)
    resp.headers.update(_cors_headers(request))
    return resp


class LocalAPI:
    """Lightweight HTTP server for receiving commands from the web frontend."""

    def __init__(
        self,
        msg_queue: queue.Queue,
        status_fn=None,
        host: str = "127.0.0.1",
        port: int = 18520,
    ) -> None:
        self._msg_queue = msg_queue
        self._status_fn = status_fn  # callable returning dict
        self._host = host
        self._port = port
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._run, name="LocalAPI", daemon=True
        )
        self._thread.start()
        logger.info("Local API starting on %s:%d", self._host, self._port)

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._serve())

    async def _serve(self) -> None:
        app = web.Application(middlewares=[cors_middleware])
        app.router.add_get("/api/status", self._handle_status)
        app.router.add_post("/api/import", self._handle_import)
        app.router.add_post("/api/select", self._handle_select)

        runner = web.AppRunner(app)
        await runner.setup()
        try:
            site = web.TCPSite(runner, self._host, self._port)
            await site.start()
            logger.info("Local API listening on http://%s:%d", self._host, self._port)
            # Run forever until thread is killed (daemon)
            while True:
                await asyncio.sleep(3600)
        except OSError as exc:
            logger.error("Local API failed to bind: %s", exc)
        finally:
            await runner.cleanup()

    async def _handle_status(self, _request: web.Request) -> web.Response:
        status = self._status_fn() if self._status_fn else {"version": "1.0.0"}
        return web.json_response(status)

    async def _handle_import(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except (json.JSONDecodeError, Exception):
            return web.json_response({"error": "Invalid JSON"}, status=400)

        avatar_id = body.get("avatar_id")
        if not avatar_id:
            return web.json_response({"error": "avatar_id required"}, status=400)

        server_url = body.get("server_url", "")
        self._msg_queue.put({
            "action": "import",
            "avatar_id": avatar_id,
            "server_url": server_url,
        })
        return web.json_response({"ok": True})

    async def _handle_select(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
        except (json.JSONDecodeError, Exception):
            return web.json_response({"error": "Invalid JSON"}, status=400)

        avatar_id = body.get("avatar_id")
        if not avatar_id:
            return web.json_response({"error": "avatar_id required"}, status=400)

        self._msg_queue.put({
            "action": "select",
            "avatar_id": avatar_id,
        })
        return web.json_response({"ok": True})
