"""Helpers for comparing Nexus benchmark outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

_DEFAULT_CASES = (
    "run_code:trivial",
    "run_code:tools_search",
    "search_tools:list",
    "get_tool:primary",
)


def summarize_comparison(
    payloads: Mapping[str, Mapping[str, Any]],
    *,
    baseline_label: str,
    focus_label: str,
    case_names: tuple[str, ...] = _DEFAULT_CASES,
) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for case in case_names:
        row: dict[str, float] = {}
        present = False
        for label, payload in payloads.items():
            match = next((item for item in payload.get("cases", payload.get("results", [])) if item.get("name") == case), None)
            if match is None:
                continue
            row[label] = float(match["meanMs"])
            present = True
        if not present or baseline_label not in row or focus_label not in row:
            continue
        base = row[baseline_label]
        row[f"{focus_label}_vs_{baseline_label}_pct"] = ((base - row[focus_label]) / base) * 100.0
        summary[case] = row
    return summary


def render_markdown_report(
    summary: Mapping[str, Mapping[str, float]],
    *,
    baseline_label: str,
    focus_label: str,
) -> str:
    lines = [
        "# Nexus benchmark comparison",
        "",
        f"Baseline: `{baseline_label}`",
        f"Focus: `{focus_label}`",
        "",
        "| Case | Baseline mean ms | Focus mean ms | Improvement |",
        "| --- | ---: | ---: | ---: |",
    ]
    pct_key = f"{focus_label}_vs_{baseline_label}_pct"
    for case, row in summary.items():
        if baseline_label not in row or focus_label not in row or pct_key not in row:
            continue
        lines.append(
            f"| `{case}` | {row[baseline_label]:.3f} | {row[focus_label]:.3f} | {row[pct_key]:.1f}% |"
        )
    return "\n".join(lines) + "\n"


def write_markdown_report(markdown: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


def load_benchmark_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
