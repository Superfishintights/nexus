"""Render markdown reports for the media-household benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _load(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def render_media_household_markdown(
    benchmark: Mapping[str, Any],
    repeatability: Mapping[str, Any] | None = None,
) -> str:
    serial = benchmark.get('serial', {})
    parallel = benchmark.get('parallel', {})
    serial_wall = float(serial.get('wallMs', 0.0))
    parallel_wall = float(parallel.get('wallMs', 0.0))
    speedup_pct = ((serial_wall - parallel_wall) / serial_wall * 100.0) if serial_wall else 0.0

    lines = [
        '# Media household benchmark report',
        '',
        f"Generated: `{benchmark.get('generatedAt', 'unknown')}`",
        '',
        '## Wall-clock summary',
        '',
        f'- Serial wall time: `{serial_wall:.1f} ms`',
        f'- Parallel wall time: `{parallel_wall:.1f} ms`',
        f'- Parallel speedup: `{speedup_pct:.1f}%`',
        '',
        '## Scenario results',
        '',
    ]

    by_name = {step['name']: step['result'] for step in parallel.get('steps', [])}
    for name in ['tautulli:How I Met Your Mother', 'tautulli:Smallville']:
        result = by_name.get(name)
        if not result:
            continue
        lines.extend([
            f"### {result['show']}",
            '',
            f"- User: `{result['user']}`",
            f"- Days watched: `{result['days']}`",
            f"- Entries: `{result['entries']}`",
            f"- Avg hours/day: `{result['avgHoursPerDay']:.4f}`",
            f"- Avg episodes/day: `{result['avgEpisodesPerDay']:.4f}`",
            '',
        ])

    the_boys = by_name.get('sonarr:The Boys')
    if the_boys:
        lines.extend([
            '### Sonarr: The Boys',
            '',
            f"- Added: `{the_boys['isAdded']}`",
            f"- Match count: `{len(the_boys.get('matches', []))}`",
            '',
        ])

    n8n_steps = [step for step in parallel.get('steps', []) if step['category'] == 'n8n']
    if n8n_steps:
        lines.extend([
            '### n8n workflows',
            '',
            '| Workflow | Active | Trigger count | Latest execution status | Latest execution id | Mode |',
            '| --- | ---: | ---: | --- | --- | --- |',
        ])
        for step in sorted(n8n_steps, key=lambda item: item['name']):
            result = step['result']
            latest = result.get('latestSuccessfulExecution') or {}
            lines.append(
                f"| {result.get('name')} | {result.get('active')} | {result.get('triggerCount')} | {latest.get('status')} | {latest.get('id')} | {result.get('executionMode')} |"
            )
        lines.extend([
            '',
            '> Note: these workflow rows currently record the latest successful published execution summaries.',
            '> Direct on-demand execution of these schedule-triggered workflows is not exposed by the currently supported Nexus/n8n API surface used here.',
            '',
        ])

    if repeatability:
        lines.extend([
            '## Repeatability',
            '',
            f"- Serial mean wall time: `{float(repeatability.get('serialMeanMs', 0.0)):.1f} ms`",
            f"- Serial median wall time: `{float(repeatability.get('serialMedianMs', 0.0)):.1f} ms`",
            f"- Parallel mean wall time: `{float(repeatability.get('parallelMeanMs', 0.0)):.1f} ms`",
            f"- Parallel median wall time: `{float(repeatability.get('parallelMedianMs', 0.0)):.1f} ms`",
            '',
            '| Run | Serial ms | Parallel ms |',
            '| --- | ---: | ---: |',
        ])
        for run in repeatability.get('runs', []):
            lines.append(f"| {run['run']} | {float(run['serialWallMs']):.1f} | {float(run['parallelWallMs']):.1f} |")
        lines.append('')

    return '\n'.join(lines) + '\n'


def write_media_household_markdown(markdown: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding='utf-8')
    return path


def main() -> int:
    benchmark_path = Path('.omx/benchmarks/media-household.json')
    repeatability_path = Path('.omx/benchmarks/media-household-repeatability.json')
    benchmark = _load(benchmark_path)
    repeatability = _load(repeatability_path) if repeatability_path.exists() else None
    markdown = render_media_household_markdown(benchmark, repeatability)
    output = Path('.omx/benchmarks/media-household.md')
    write_media_household_markdown(markdown, output)
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
