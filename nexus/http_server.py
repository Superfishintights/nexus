"""Streamable HTTP entrypoint for the Nexus MCP server."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from nexus.env import get_setting
from nexus.file_staging import FileStagingService, load_file_staging_config
from nexus.http_auth import build_verifier_from_env
from nexus.server import mcp


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_PATH = "/mcp"


async def healthz(_request):
    return JSONResponse({"status": "ok"})


def _http_path_from_env() -> str:
    path = (get_setting("NEXUS_HTTP_PATH") or DEFAULT_PATH).strip() or DEFAULT_PATH
    if not path.startswith("/"):
        path = f"/{path}"
    return path


def _http_port_from_env() -> int:
    return int(get_setting("NEXUS_HTTP_PORT") or str(DEFAULT_PORT))


def create_app() -> Starlette:
    verifier = build_verifier_from_env()
    http_path = _http_path_from_env()
    staging_config = load_file_staging_config()
    staging = FileStagingService(staging_config, verifier) if staging_config else None
    previous_auth = mcp.auth
    mcp.auth = verifier
    try:
        mcp_app = mcp.http_app(
            path=http_path,
            stateless_http=False,
            json_response=False,
            host_origin_protection="auto",
        )
    finally:
        mcp.auth = previous_auth
    @asynccontextmanager
    async def lifespan(app):
        async with mcp_app.lifespan(app):
            if staging is not None:
                staging.start()
            try:
                yield
            finally:
                if staging is not None:
                    await staging.stop()

    routes = [Route("/healthz", healthz, methods=["GET"])]
    if staging is not None:
        routes.extend(
            [
                Route("/files", staging.upload, methods=["POST"]),
                Route("/files/{artifact_id}", staging.delete, methods=["DELETE"]),
            ]
        )
    routes.append(Mount("/", app=mcp_app))
    return Starlette(lifespan=lifespan, routes=routes)


def main() -> None:
    verifier = build_verifier_from_env()
    if not verifier.has_tokens:
        print(
            "Nexus HTTP bearer auth is required: set NEXUS_HTTP_BEARER_TOKENS "
            "or NEXUS_HTTP_BEARER_TOKEN before serving.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    uvicorn.run(
        create_app(),
        host=get_setting("NEXUS_HTTP_HOST") or DEFAULT_HOST,
        port=_http_port_from_env(),
    )


if __name__ == "__main__":
    main()
