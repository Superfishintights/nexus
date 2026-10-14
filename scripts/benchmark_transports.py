#!/usr/bin/env python3
"""Benchmark equivalent Nexus MCP calls over stdio and Streamable HTTP."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


GATEWAY_TOOLS = {
    "get_tool",
    "list_tool_namespaces",
    "run_code",
    "search_tools",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http-url", required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--stdio-python", type=Path, required=True)
    parser.add_argument("--stdio-cwd", type=Path, required=True)
    parser.add_argument("--warm-iterations", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--cold-iterations", type=int, default=10)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    return parser.parse_args()


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def summarize(values: list[float], last_result: Any) -> dict[str, Any]:
    return {
        "n": len(values),
        "min_ms": round(min(values), 3),
        "mean_ms": round(statistics.fmean(values), 3),
        "p50_ms": round(percentile(values, 0.50), 3),
        "p95_ms": round(percentile(values, 0.95), 3),
        "max_ms": round(max(values), 3),
        "last_result": last_result,
    }


def parse_tool_result(result: Any) -> dict[str, Any]:
    return json.loads(result.content[0].text)


async def timed_calls(
    operation: Callable[[], Awaitable[Any]],
    *,
    warmups: int,
    iterations: int,
) -> dict[str, Any]:
    for _ in range(warmups):
        await operation()
    timings: list[float] = []
    last_result: Any = None
    for _ in range(iterations):
        started = time.perf_counter_ns()
        last_result = await operation()
        timings.append((time.perf_counter_ns() - started) / 1_000_000)
    return summarize(timings, last_result)


async def benchmark_warm(client: Client, warmups: int, iterations: int) -> dict[str, Any]:
    async def list_tools() -> int:
        return len(await client.list_tools())

    async def list_namespaces() -> int:
        payload = parse_tool_result(await client.call_tool("list_tool_namespaces", {}))
        return len(payload["namespaces"])

    async def search_all() -> int:
        payload = parse_tool_result(
            await client.call_tool(
                "search_tools",
                {"query": "", "detail_level": "name", "limit": 10_000},
            )
        )
        return len(payload["tools"])

    async def search_namespace() -> int:
        payload = parse_tool_result(
            await client.call_tool(
                "search_tools",
                {
                    "query": "",
                    "detail_level": "name",
                    "limit": 10_000,
                    "namespace": "sonarr",
                },
            )
        )
        return len(payload["tools"])

    async def get_tool() -> str:
        payload = parse_tool_result(
            await client.call_tool("get_tool", {"name": "jira.get_issue_status"})
        )
        return payload["tool"]["name"]

    async def run_code() -> int:
        payload = parse_tool_result(
            await client.call_tool("run_code", {"code": "RESULT = 2 + 2"})
        )
        return payload["result"]

    cases = {
        "list_tools": list_tools,
        "list_tool_namespaces": list_namespaces,
        "search_tools_all_names": search_all,
        "search_tools_namespace": search_namespace,
        "get_tool": get_tool,
        "run_code_trivial": run_code,
    }
    return {
        name: await timed_calls(operation, warmups=warmups, iterations=iterations)
        for name, operation in cases.items()
    }


async def inspect_surface(client: Client) -> dict[str, Any]:
    tool_names = sorted(tool.name for tool in await client.list_tools())
    namespace_payload = parse_tool_result(
        await client.call_tool("list_tool_namespaces", {})
    )
    search_payload = parse_tool_result(
        await client.call_tool(
            "search_tools",
            {"query": "", "detail_level": "name", "limit": 10_000},
        )
    )
    return {
        "tool_names": tool_names,
        "namespaces": namespace_payload["namespaces"],
        "search_names": sorted(item["name"] for item in search_payload["tools"]),
    }


async def cold_benchmark(factory: Callable[[], Client], iterations: int) -> dict[str, Any]:
    timings: list[float] = []
    tool_count = 0
    for _ in range(iterations):
        started = time.perf_counter_ns()
        async with factory() as client:
            tool_count = len(await client.list_tools())
        timings.append((time.perf_counter_ns() - started) / 1_000_000)
    result = summarize(timings, tool_count)
    result["tool_count"] = result.pop("last_result")
    return result


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Nexus stdio vs Streamable HTTP benchmark",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "| Measurement | Stdio p50 ms | Stdio p95 ms | HTTP p50 ms | HTTP p95 ms |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, stdio in report["warm"]["stdio"].items():
        http = report["warm"]["http_ct108"][name]
        lines.append(
            f"| `{name}` | {stdio['p50_ms']:.3f} | {stdio['p95_ms']:.3f} | "
            f"{http['p50_ms']:.3f} | {http['p95_ms']:.3f} |"
        )
    cold = report["cold_connect_list_tools"]
    lines.extend(
        [
            "",
            "| Cold path | Stdio p50 ms | Stdio p95 ms | HTTP p50 ms | HTTP p95 ms |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| connect + `list_tools` | {cold['stdio']['p50_ms']:.3f} | "
            f"{cold['stdio']['p95_ms']:.3f} | {cold['http_ct108']['p50_ms']:.3f} | "
            f"{cold['http_ct108']['p95_ms']:.3f} |",
            "",
            f"Surface parity: `{report['parity']}`",
            "",
        ]
    )
    return "\n".join(lines)


async def run(args: argparse.Namespace) -> dict[str, Any]:
    token = args.token_file.read_text(encoding="utf-8").strip()
    stdio_env = {
        **os.environ,
        "FASTMCP_LOG_LEVEL": "ERROR",
        "FASTMCP_CHECK_FOR_UPDATES": "off",
    }

    def stdio_client() -> Client:
        return Client(
            StdioTransport(
                command=str(args.stdio_python),
                args=["-m", "nexus.server"],
                cwd=str(args.stdio_cwd),
                env=stdio_env,
            )
        )

    def http_client() -> Client:
        return Client(args.http_url, auth=token)

    async with stdio_client() as client:
        stdio_surface = await inspect_surface(client)
        stdio_warm = await benchmark_warm(client, args.warmups, args.warm_iterations)
    async with http_client() as client:
        http_surface = await inspect_surface(client)
        http_warm = await benchmark_warm(client, args.warmups, args.warm_iterations)

    expected_tools = sorted(GATEWAY_TOOLS)
    parity = {
        "gateway_tools": stdio_surface["tool_names"] == http_surface["tool_names"] == expected_tools,
        "namespace_payload": stdio_surface["namespaces"] == http_surface["namespaces"],
        "canonical_tool_names": stdio_surface["search_names"] == http_surface["search_names"],
        "namespace_count": len(http_surface["namespaces"]),
        "canonical_tool_count": len(http_surface["search_names"]),
    }
    if not all(parity[key] for key in ("gateway_tools", "namespace_payload", "canonical_tool_names")):
        raise RuntimeError(f"refusing to benchmark non-equivalent surfaces: {parity}")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "local_stdio": {
            "command": f"{args.stdio_python} -m nexus.server",
            "cwd": str(args.stdio_cwd),
        },
        "remote_http": {"url": args.http_url, "host": "ct108"},
        "warm_iterations": args.warm_iterations,
        "warmups": args.warmups,
        "cold_iterations": args.cold_iterations,
        "parity": parity,
        "warm": {"stdio": stdio_warm, "http_ct108": http_warm},
        "cold_connect_list_tools": {
            "stdio": await cold_benchmark(stdio_client, args.cold_iterations),
            "http_ct108": await cold_benchmark(http_client, args.cold_iterations),
        },
    }


def main() -> None:
    args = parse_args()
    if min(args.warm_iterations, args.cold_iterations) < 1 or args.warmups < 0:
        raise SystemExit("iteration counts must be positive and warmups non-negative")
    report = asyncio.run(run(args))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    rendered = markdown(report)
    args.output_markdown.write_text(rendered, encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
