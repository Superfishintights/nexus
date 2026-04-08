"""Phase-1 benchmark/eval baseline harness for Nexus."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .runner import run_user_code
from .tool_catalog import get_catalog, resolve_tool_request, search_catalog, spec_to_dict
from .tool_registry import get_tool as get_loaded_tool, is_tool_loaded
from .tool_policy import get_active_tool_policy


@dataclass(frozen=True)
class BenchmarkSample:
    name: str
    duration_ms: float


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    call: Callable[[], object]
    category: str
    detail: str


def summarize_samples(samples: Iterable[float]) -> Dict[str, float]:
    values = list(samples)
    if not values:
        return {
            "iterations": 0,
            "minMs": 0.0,
            "maxMs": 0.0,
            "meanMs": 0.0,
            "medianMs": 0.0,
        }
    return {
        "iterations": len(values),
        "minMs": min(values),
        "maxMs": max(values),
        "meanMs": statistics.fmean(values),
        "medianMs": statistics.median(values),
    }


def benchmark_case(case: BenchmarkCase, *, iterations: int, warmups: int) -> Dict[str, Any]:
    for _ in range(max(0, warmups)):
        case.call()

    samples: List[BenchmarkSample] = []
    for _ in range(max(1, iterations)):
        started = time.perf_counter()
        case.call()
        samples.append(BenchmarkSample(case.name, (time.perf_counter() - started) * 1000.0))

    durations = [sample.duration_ms for sample in samples]
    return {
        "name": case.name,
        "category": case.category,
        "detail": case.detail,
        "latenciesMs": durations,
        **summarize_samples(durations),
    }


def _search_tools_payload(query: str, *, limit: int) -> Dict[str, Any]:
    policy = get_active_tool_policy()
    matches = search_catalog(query, limit=limit, policy=policy)
    return {
        "query": query,
        "totalMatches": len(matches),
        "tools": [spec_to_dict(spec, detail_level="summary", loaded=is_tool_loaded(spec.name)) for spec in matches],
        "policy": policy.to_dict(),
    }


def _get_tool_payload(name: str) -> Dict[str, Any]:
    policy = get_active_tool_policy()
    catalog = get_catalog(refresh=True)
    spec = resolve_tool_request(name, catalog=catalog, policy=policy, allow_aliases=not policy.is_restricted)
    payload = spec_to_dict(spec, detail_level="full", loaded=is_tool_loaded(spec.name))
    if is_tool_loaded(spec.name):
        info = get_loaded_tool(spec.name)
        payload["module"] = info.module
        payload["signature"] = info.signature
        payload["description"] = info.description
        payload["examples"] = list(info.examples)
    return {"tool": payload, "policy": policy.to_dict()}


def default_cases(*, tool_name: Optional[str] = None) -> List[BenchmarkCase]:
    catalog = get_catalog(refresh=True)
    discoverable_names = [name for name, spec in catalog.items() if spec.alias_of is None]
    selected_tool = tool_name or (discoverable_names[0] if discoverable_names else None)

    cases = [
        BenchmarkCase(
            name="search_tools:list",
            category="catalog",
            detail="search_tools empty-query listing",
            call=lambda: _search_tools_payload("", limit=20),
        ),
        BenchmarkCase(
            name="run_code:trivial",
            category="runner",
            detail="run_code arithmetic snippet",
            call=lambda: run_user_code("RESULT = 2 + 2").result,
        ),
        BenchmarkCase(
            name="run_code:tools_search",
            category="runner",
            detail="run_code snippet that searches TOOLS lazily",
            call=lambda: run_user_code("RESULT = TOOLS.search('', limit=5)").result,
        ),
    ]
    if selected_tool:
        cases.insert(
            1,
            BenchmarkCase(
                name="get_tool:primary",
                category="catalog",
                detail=f"get_tool for {selected_tool}",
                call=lambda selected_tool=selected_tool: _get_tool_payload(selected_tool),
            ),
        )
    return cases


def run_phase1_benchmarks(
    *,
    iterations: int = 5,
    warmups: int = 1,
    tool_name: Optional[str] = None,
) -> Dict[str, Any]:
    report_cases = [benchmark_case(case, iterations=iterations, warmups=warmups) for case in default_cases(tool_name=tool_name)]
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
        "policy": get_active_tool_policy().to_dict(),
        "iterations": iterations,
        "warmups": warmups,
        "cases": report_cases,
    }


def default_output_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(".omx") / "benchmarks" / f"phase1-baseline-{timestamp}.json"


def write_report(report: Mapping[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--tool-name", default=None)
    parser.add_argument("--output", default=None, help="Write machine-readable benchmark output to this path")
    args = parser.parse_args(argv)

    report = run_phase1_benchmarks(
        iterations=args.iterations,
        warmups=args.warmups,
        tool_name=args.tool_name,
    )
    output_path = Path(args.output) if args.output else default_output_path()
    write_report(report, output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
