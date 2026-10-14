from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


GATEWAY_TOOL_NAMES = {
    "run_code",
    "search_tools",
    "get_tool",
    "list_tool_namespaces",
}
REPO_ROOT = Path(__file__).resolve().parents[1]


def _base_server_env(tmp_path: Path) -> dict[str, str]:
    env_file = tmp_path / "empty.env"
    env_file.write_text("", encoding="utf-8")
    env = {
        **os.environ,
        "NEXUS_ENV_FILE": str(env_file),
        "NEXUS_TOOL_PACKAGES": "nexus_tools_jira,nexus_tools_n8n",
        "NEXUS_TOOL_POLICY_MODE": "unrestricted",
        "FASTMCP_LOG_LEVEL": "ERROR",
        "FASTMCP_CHECK_FOR_UPDATES": "off",
    }
    env.pop("NEXUS_TOOL_POLICY_PRESET", None)
    return env


def _file_staging_env(tmp_path: Path) -> dict[str, str]:
    env = {
        **_base_server_env(tmp_path),
        "NEXUS_HTTP_HOST": "127.0.0.1",
        "NEXUS_HTTP_PORT": str(_free_port()),
        "NEXUS_HTTP_PATH": "/mcp",
        "NEXUS_HTTP_BEARER_TOKENS": "alpha,beta",
        "NEXUS_FILE_STAGING_ROOT": str(tmp_path / "staged"),
        "NEXUS_FILE_STAGING_MAX_BYTES": "1024",
        "NEXUS_FILE_STAGING_QUOTA_BYTES": "2048",
        "NEXUS_FILE_STAGING_TTL_SECONDS": "60",
    }
    return env


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def nexus_http_server(tmp_path: Path) -> Iterator[str]:
    port = _free_port()
    env = {
        **_base_server_env(tmp_path),
        "NEXUS_HTTP_HOST": "127.0.0.1",
        "NEXUS_HTTP_PORT": str(port),
        "NEXUS_HTTP_PATH": "/mcp",
        "NEXUS_HTTP_BEARER_TOKENS": "alpha,beta",
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "nexus.http_server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                stderr = proc.stderr.read() if proc.stderr else ""
                raise RuntimeError(f"Nexus HTTP server exited early: {stderr}")
            try:
                response = httpx.get(f"{base_url}/healthz", timeout=0.5)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Timed out waiting for Nexus HTTP server health")
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def test_main_requires_bearer_token() -> None:
    env = {
        **os.environ,
        "NEXUS_HTTP_HOST": "127.0.0.1",
        "NEXUS_HTTP_PORT": str(_free_port()),
        "NEXUS_HTTP_PATH": "/mcp",
        "FASTMCP_LOG_LEVEL": "ERROR",
        "FASTMCP_CHECK_FOR_UPDATES": "off",
    }
    env.pop("NEXUS_HTTP_BEARER_TOKEN", None)
    env.pop("NEXUS_HTTP_BEARER_TOKENS", None)

    proc = subprocess.run(
        [sys.executable, "-m", "nexus.http_server"],
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )

    assert proc.returncode == 2
    assert "NEXUS_HTTP_BEARER_TOKENS" in proc.stderr


def test_health_is_unauthenticated(nexus_http_server: str) -> None:
    response = httpx.get(f"{nexus_http_server}/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_mcp_requires_bearer_token(nexus_http_server: str) -> None:
    response = httpx.post(f"{nexus_http_server}/mcp", json={"jsonrpc": "2.0"})

    assert response.status_code == 401


def test_valid_client_lists_and_calls_gateway_tools(nexus_http_server: str) -> None:
    asyncio.run(_assert_valid_client_lists_and_calls_gateway_tools(nexus_http_server))


async def _assert_valid_client_lists_and_calls_gateway_tools(
    nexus_http_server: str,
) -> None:
    async with Client(f"{nexus_http_server}/mcp", auth="alpha") as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools}

        assert names == GATEWAY_TOOL_NAMES

        search_result = await client.call_tool(
            "search_tools",
            {"query": "", "detail_level": "name", "limit": 10_000},
        )
        search_payload = json.loads(search_result.content[0].text)
        assert search_payload["success"] is True
        assert search_payload["query"] == ""
        assert isinstance(search_payload["tools"], list)

        namespace_search_result = await client.call_tool(
            "search_tools",
            {
                "query": "",
                "detail_level": "name",
                "limit": 10_000,
                "namespace": "jira",
            },
        )
        namespace_search_payload = json.loads(namespace_search_result.content[0].text)
        assert namespace_search_payload["namespace"] == "jira"
        assert [tool["name"] for tool in namespace_search_payload["tools"]] == [
            "jira.get_issue_status"
        ]

        namespaces_result = await client.call_tool("list_tool_namespaces", {})
        namespaces_payload = json.loads(namespaces_result.content[0].text)
        assert namespaces_payload["success"] is True
        assert [entry["name"] for entry in namespaces_payload["namespaces"]] == [
            "jira",
            "n8n",
        ]
        assert [entry["tool_count"] for entry in namespaces_payload["namespaces"]] == [
            1,
            60,
        ]
        assert all(
            set(entry) == {"name", "display_name", "description", "tool_count"}
            for entry in namespaces_payload["namespaces"]
        )
        assert all(
            len(entry["description"]) <= 240
            for entry in namespaces_payload["namespaces"]
        )

        run_result = await client.call_tool("run_code", {"code": "RESULT = 2 + 2"})
        run_payload = json.loads(run_result.content[0].text)
        assert run_payload["success"] is True
        assert run_payload["result"] == 4


def test_stdio_and_http_expose_the_same_exact_gateway_surface(
    nexus_http_server: str,
    tmp_path: Path,
) -> None:
    asyncio.run(
        _assert_stdio_and_http_expose_the_same_exact_gateway_surface(
            nexus_http_server,
            tmp_path,
        )
    )


async def _assert_stdio_and_http_expose_the_same_exact_gateway_surface(
    nexus_http_server: str,
    tmp_path: Path,
) -> None:
    stdio_transport = StdioTransport(
        command=sys.executable,
        args=["-m", "nexus.server"],
        env=_base_server_env(tmp_path),
        cwd=str(REPO_ROOT),
    )
    async with Client(stdio_transport) as stdio_client:
        stdio_names = {tool.name for tool in await stdio_client.list_tools()}
    async with Client(f"{nexus_http_server}/mcp", auth="alpha") as http_client:
        http_names = {tool.name for tool in await http_client.list_tools()}

    assert stdio_names == http_names == GATEWAY_TOOL_NAMES


def test_two_tokens_can_call_concurrently(nexus_http_server: str) -> None:
    asyncio.run(_assert_two_tokens_can_call_concurrently(nexus_http_server))


async def _assert_two_tokens_can_call_concurrently(nexus_http_server: str) -> None:
    async def call(token: str, value: int) -> int:
        async with Client(f"{nexus_http_server}/mcp", auth=token) as client:
            result = await client.call_tool(
                "run_code",
                {"code": f"RESULT = {value}"},
            )
            payload = json.loads(result.content[0].text)
            assert payload["success"] is True
            return payload["result"]

    results = await asyncio.gather(call("alpha", 41), call("beta", 42))

    assert results == [41, 42]


def test_file_staging_is_not_an_mcp_tool(nexus_http_server: str) -> None:
    asyncio.run(_assert_file_staging_is_not_an_mcp_tool(nexus_http_server))


async def _assert_file_staging_is_not_an_mcp_tool(nexus_http_server: str) -> None:
    async with Client(f"{nexus_http_server}/mcp", auth="alpha") as client:
        names = {tool.name for tool in await client.list_tools()}
    assert names == GATEWAY_TOOL_NAMES


@pytest.fixture
def nexus_http_file_server(tmp_path: Path) -> Iterator[tuple[str, Path]]:
    env = _file_staging_env(tmp_path)
    proc = subprocess.Popen(
        [sys.executable, "-m", "nexus.http_server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{env['NEXUS_HTTP_PORT']}"
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                stderr = proc.stderr.read() if proc.stderr else ""
                raise RuntimeError(f"Nexus HTTP server exited early: {stderr}")
            try:
                response = httpx.get(f"{base_url}/healthz", timeout=0.5)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Timed out waiting for Nexus HTTP server health")
        yield base_url, Path(env["NEXUS_FILE_STAGING_ROOT"])
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def test_file_upload_requires_bearer_token(nexus_http_file_server: tuple[str, Path]) -> None:
    base_url, _root = nexus_http_file_server

    response = httpx.post(
        f"{base_url}/files",
        content=b"hello",
        headers={"X-Nexus-Filename": "hello.txt", "Content-Type": "text/plain"},
    )

    assert response.status_code == 401


def test_file_upload_rejects_traversal_and_blocked_extension(
    nexus_http_file_server: tuple[str, Path],
) -> None:
    base_url, _root = nexus_http_file_server

    traversal = httpx.post(
        f"{base_url}/files",
        content=b"hello",
        headers={
            "Authorization": "Bearer alpha",
            "X-Nexus-Filename": "../hello.txt",
            "Content-Type": "text/plain",
            "Content-Length": "5",
        },
    )
    blocked = httpx.post(
        f"{base_url}/files",
        content=b"hello",
        headers={
            "Authorization": "Bearer alpha",
            "X-Nexus-Filename": "run.sh",
            "Content-Type": "text/plain",
            "Content-Length": "5",
        },
    )

    assert traversal.status_code == 400
    assert traversal.json()["error"] == "invalid_filename"
    assert blocked.status_code == 400
    assert blocked.json()["error"] == "extension_not_allowed"


def test_file_upload_delete_and_client_separation(
    nexus_http_file_server: tuple[str, Path],
) -> None:
    base_url, root = nexus_http_file_server

    first = httpx.post(
        f"{base_url}/files",
        content=b"<p>alpha</p>",
        headers={
            "Authorization": "Bearer alpha",
            "X-Nexus-Filename": "sample.html",
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": "12",
        },
    )
    second = httpx.post(
        f"{base_url}/files",
        content=b"beta",
        headers={
            "Authorization": "Bearer beta",
            "X-Nexus-Filename": "sample.txt",
            "Content-Type": "text/plain",
            "Content-Length": "4",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["artifact_id"] != second_payload["artifact_id"]
    assert Path(first_payload["path"]).read_bytes() == b"<p>alpha</p>"
    assert Path(first_payload["path"]).stat().st_mode & 0o777 == 0o600
    assert Path(first_payload["path"]).is_relative_to(root)
    assert Path(first_payload["path"]).parent != Path(second_payload["path"]).parent

    wrong_client_delete = httpx.delete(
        f"{base_url}/files/{first_payload['artifact_id']}",
        headers={"Authorization": "Bearer beta"},
    )
    assert wrong_client_delete.json()["deleted"] is False
    assert Path(first_payload["path"]).exists()
    assert not (Path(second_payload["path"]).parent / "metadata" / f"{first_payload['artifact_id']}.json").exists()

    delete_response = httpx.delete(
        f"{base_url}/files/{first_payload['artifact_id']}",
        headers={"Authorization": "Bearer alpha"},
    )
    assert delete_response.json()["deleted"] is True
    assert not Path(first_payload["path"]).exists()


def test_file_upload_size_limit(nexus_http_file_server: tuple[str, Path]) -> None:
    base_url, _root = nexus_http_file_server

    response = httpx.post(
        f"{base_url}/files",
        content=b"x" * 1025,
        headers={
            "Authorization": "Bearer alpha",
            "X-Nexus-Filename": "too-big.txt",
            "Content-Type": "text/plain",
            "Content-Length": "1025",
        },
    )

    assert response.status_code == 413
    assert response.json()["error"] == "too_large"


def test_file_upload_quota_and_collision_resistance(
    nexus_http_file_server: tuple[str, Path],
) -> None:
    base_url, _root = nexus_http_file_server
    headers = {
        "Authorization": "Bearer alpha",
        "X-Nexus-Filename": "same.txt",
        "Content-Type": "text/plain",
    }

    first = httpx.post(f"{base_url}/files", content=b"a" * 900, headers=headers)
    second = httpx.post(f"{base_url}/files", content=b"b" * 900, headers=headers)
    over_quota = httpx.post(f"{base_url}/files", content=b"c" * 300, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["artifact_id"] != second.json()["artifact_id"]
    assert first.json()["path"] != second.json()["path"]
    assert over_quota.status_code == 413
    assert over_quota.json()["error"] == "quota_exceeded"


def test_file_route_has_no_download_surface(
    nexus_http_file_server: tuple[str, Path],
) -> None:
    base_url, _root = nexus_http_file_server
    response = httpx.get(
        f"{base_url}/files",
        headers={"Authorization": "Bearer alpha"},
    )

    assert response.status_code in {404, 405}


def test_file_helper_accepts_mcp_url_and_deletes_receipt(
    nexus_http_file_server: tuple[str, Path],
    tmp_path: Path,
) -> None:
    base_url, _root = nexus_http_file_server
    source = tmp_path / "helper.html"
    source.write_text("<p>helper</p>", encoding="utf-8")
    upload = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "nexus_file_stage.py"),
            "--url",
            f"{base_url}/mcp",
            "--token",
            "alpha",
            "upload",
            str(source),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    receipt = json.loads(upload.stdout)

    assert Path(receipt["path"]).read_text(encoding="utf-8") == "<p>helper</p>"

    delete = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "nexus_file_stage.py"),
            "--url",
            f"{base_url}/mcp",
            "--token",
            "alpha",
            "delete",
            receipt["artifact_id"],
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(delete.stdout)["deleted"] is True
    assert not Path(receipt["path"]).exists()
