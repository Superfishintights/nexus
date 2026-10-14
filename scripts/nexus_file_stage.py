#!/usr/bin/env python3
"""Upload/delete files through the Nexus Streamable HTTP staging endpoint."""

from __future__ import annotations

import argparse
import http.client
import json
import mimetypes
import os
import re
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


def _token(args: argparse.Namespace) -> str:
    if args.token:
        return args.token
    if args.token_file:
        return Path(args.token_file).read_text(encoding="utf-8").strip()
    token = os.getenv("NEXUS_HTTP_BEARER_TOKEN") or os.getenv("NEXUS_HTTP_TOKEN")
    if token:
        return token
    raise SystemExit("Set --token, --token-file, NEXUS_HTTP_BEARER_TOKEN, or NEXUS_HTTP_TOKEN")


def _url(args: argparse.Namespace) -> str:
    base = (args.url or os.getenv("NEXUS_HTTP_URL") or "http://127.0.0.1:8000").rstrip("/")
    if base.endswith("/mcp"):
        base = base[:-4]
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SystemExit("Nexus HTTP URL must use http:// or https:// and include a host")
    return base


def upload(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_file() or path.is_symlink():
        raise SystemExit("upload path must be a regular file and not a symlink")
    content_type = args.content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parsed = urlparse(_url(args))
    connection_class = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    connection = connection_class(parsed.hostname, parsed.port, timeout=args.timeout)
    target = f"{parsed.path.rstrip('/')}/files" if parsed.path else "/files"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    try:
        connection.putrequest("POST", target)
        connection.putheader("Authorization", f"Bearer {_token(args)}")
        connection.putheader("Content-Type", content_type)
        connection.putheader("Content-Length", str(path.stat().st_size))
        connection.putheader("X-Nexus-Filename", quote(path.name))
        connection.endheaders()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                connection.send(chunk)
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        if response.status >= 400:
            raise SystemExit(f"upload failed: HTTP {response.status} {payload}")
    finally:
        connection.close()
    if args.output == "path":
        print(payload["path"])
    else:
        print(json.dumps(payload, sort_keys=True))
    return 0


def delete(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[0-9a-f]{32}", args.artifact_id):
        raise SystemExit("artifact_id must be 32 lowercase hexadecimal characters")
    request = Request(
        f"{_url(args)}/files/{args.artifact_id}",
        method="DELETE",
        headers={"Authorization": f"Bearer {_token(args)}"},
    )
    with urlopen(request, timeout=args.timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    print(json.dumps(payload, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Nexus HTTP base URL, without /mcp")
    parser.add_argument("--token", help="Bearer token. Prefer --token-file for shell history safety.")
    parser.add_argument("--token-file", help="File containing the bearer token")
    parser.add_argument("--timeout", type=float, default=120)
    sub = parser.add_subparsers(dest="command", required=True)
    upload_parser = sub.add_parser("upload")
    upload_parser.add_argument("path")
    upload_parser.add_argument("--content-type")
    upload_parser.add_argument("--output", choices=["json", "path"], default="json")
    upload_parser.set_defaults(func=upload)
    delete_parser = sub.add_parser("delete")
    delete_parser.add_argument("artifact_id")
    delete_parser.set_defaults(func=delete)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
