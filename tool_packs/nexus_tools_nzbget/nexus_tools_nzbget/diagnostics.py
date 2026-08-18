"""NZBGet diagnostic and server-test tools."""

from __future__ import annotations

from typing import Any, Dict

from nexus.tool_registry import register_tool

from .client import get_client


@register_tool(
    namespace="nzbget",
    description="Test whether NZBGet can find an executor program for an extension script.",
    examples=['load_tool("nzbget.testextension")("Script.py")'],
    aliases=[],
)
def testextension(ext_entry_name: str) -> bool:
    """RPC signature: bool testextension(string ExtEntryName)."""
    return get_client().call("testextension", [ext_entry_name])


@register_tool(
    namespace="nzbget",
    description="Test NZBGet connectivity to a news server using supplied connection settings.",
    examples=['load_tool("nzbget.testserver")("news.example.test", 563, "user", "pass", True, "AES256-SHA", 30, 2)'],
    aliases=[],
)
def testserver(
    host: str,
    port: int,
    username: str,
    password: str,
    encryption: bool,
    cipher: str,
    timeout: int,
    cert_verification_level: int,
) -> str:
    """RPC signature: string testserver(string host, int port, string username, string password, bool encryption, string cipher, int timeout, int certVerificationLevel)."""
    return get_client().call(
        "testserver",
        [
            host,
            port,
            username,
            password,
            encryption,
            cipher,
            timeout,
            cert_verification_level,
        ],
    )


@register_tool(
    namespace="nzbget",
    description="Start an NZBGet server speed test by adding a high-priority test NZB; this creates a temporary queue item.",
    examples=['load_tool("nzbget.testserverspeed")("https://example.test/test.nzb", 1)'],
    aliases=[],
)
def testserverspeed(nzb_file_url: str, server_id: int) -> bool:
    """RPC signature: bool testserverspeed(string nzbFileUrl, int serverId)."""
    return get_client().call("testserverspeed", [nzb_file_url, server_id])


@register_tool(
    namespace="nzbget",
    description="Run an NZBGet disk speed test by writing temporary data until size or timeout limits are reached.",
    examples=['load_tool("nzbget.testdiskspeed")("/downloads/tmp", 1024, 100, 10)'],
    aliases=[],
)
def testdiskspeed(
    dir_path: str,
    write_buffer_size: int,
    max_file_size: int,
    timeout: int,
) -> Dict[str, Any]:
    """RPC signature: struct testdiskspeed(string dirPath, int writeBufferSize, int maxFileSize, int timeout)."""
    return get_client().call(
        "testdiskspeed",
        [dir_path, write_buffer_size, max_file_size, timeout],
    )


@register_tool(
    namespace="nzbget",
    description="Start the NZBGet network speed test.",
    examples=['load_tool("nzbget.testnetworkspeed")()'],
    aliases=[],
)
def testnetworkspeed() -> Dict[str, Any]:
    """RPC signature: struct testnetworkspeed()."""
    return get_client().call("testnetworkspeed")
