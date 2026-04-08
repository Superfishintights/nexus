"""Real-world media/tool benchmark scenario for Nexus."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

from .runner import RunnerLimits, run_user_code

DEFAULT_USER = "SuperJayintights"
DEFAULT_SHOWS = ("How I Met Your Mother", "Smallville")
DEFAULT_SONARR_TITLE = "The Boys"

TAUTULLI_TEMPLATE = '''
users = load_tool("tautulli.get_users")()['data']
user_id = None
for entry in users:
    if entry.get('friendly_name') == {user_name!r}:
        user_id = entry.get('user_id')
        break
history_tool = load_tool('tautulli.get_history')
all_rows = []
start = 0
page = 250
while True:
    batch = history_tool(user_id=user_id, length=page, start=start)
    rows = batch.get('data', [])
    if not rows:
        break
    all_rows.extend(rows)
    if len(rows) < page:
        break
    start += page
show = {show_name!r}
daily = {{}}
for row in all_rows:
    if row.get('media_type') != 'episode':
        continue
    if row.get('grandparent_title') != show:
        continue
    day = row.get('started', row.get('date'))
    day = __import__('datetime').datetime.utcfromtimestamp(day).strftime('%Y-%m-%d')
    bucket = daily.setdefault(day, {{'seconds': 0, 'episodes': 0}})
    bucket['seconds'] += int(row.get('play_duration') or row.get('duration') or 0)
    bucket['episodes'] += 1
seconds_total = 0
episode_total = 0
for bucket in daily.values():
    seconds_total += bucket['seconds']
    episode_total += bucket['episodes']
day_count = len(daily)
RESULT = {{
    'user': {user_name!r},
    'show': show,
    'days': day_count,
    'entries': episode_total,
    'avgHoursPerDay': (seconds_total / 3600.0 / day_count) if day_count else 0,
    'avgEpisodesPerDay': (episode_total / day_count) if day_count else 0,
}}
'''

N8N_TEMPLATE = '''
workflows = load_tool('n8n.get_workflows')(active=True)
executions = load_tool('n8n.get_executions')
target = None
for workflow in workflows:
    if workflow.get('id') == {workflow_id!r}:
        target = workflow
        break
latest = executions(limit=1, status='success', workflow_id={workflow_id!r})
RESULT = {{
    'id': {workflow_id!r},
    'name': target.get('name') if target else None,
    'active': target.get('active') if target else None,
    'triggerCount': target.get('triggerCount') if target else None,
    'latestSuccessfulExecution': latest[0] if latest else None,
    'executionMode': 'latest_success_summary',
    'executionNote': 'Current supported n8n public API/tools do not expose on-demand execution for these published schedule-triggered workflows.',
}}
'''

SONARR_TEMPLATE = '''
series = load_tool("sonarr.get_series")()
needle = {title!r}.lower()
matches = []
for item in series:
    title = str(item.get('title', '')).lower()
    if title == needle or needle in title:
        matches.append({{
            'title': item.get('title'),
            'status': item.get('status'),
            'monitored': item.get('monitored'),
            'id': item.get('id'),
        }})
RESULT = {{
    'title': {title!r},
    'isAdded': len(matches) > 0,
    'matches': matches,
}}
'''


@dataclass(frozen=True)
class ScenarioStep:
    name: str
    category: str
    code: str
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class StepResult:
    name: str
    category: str
    elapsed_ms: float
    result: Any


def _timed_run(step: ScenarioStep) -> StepResult:
    started = time.perf_counter()
    result = run_user_code(
        step.code,
        limits=RunnerLimits(timeout_seconds=step.timeout_seconds, max_stdout_chars=32000, max_result_chars=64000),
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    return StepResult(
        name=step.name,
        category=step.category,
        elapsed_ms=elapsed_ms,
        result=result.result,
    )


def build_steps(
    *,
    user_name: str = DEFAULT_USER,
    sonarr_title: str = DEFAULT_SONARR_TITLE,
    workflow_ids: Optional[List[str]] = None,
) -> List[ScenarioStep]:
    steps = [
        ScenarioStep(
            name=f"tautulli:{show}",
            category="tautulli",
            code=TAUTULLI_TEMPLATE.format(user_name=user_name, show_name=show),
        )
        for show in DEFAULT_SHOWS
    ]
    active_workflow_ids = workflow_ids or ["aCc9YEwBJ59sXPqE", "lFLvRtjncYmDpNQu"]
    for workflow_id in active_workflow_ids:
        steps.append(
            ScenarioStep(
                name=f"n8n:{workflow_id}",
                category="n8n",
                code=N8N_TEMPLATE.format(workflow_id=workflow_id),
            )
        )
    steps.append(
        ScenarioStep(
            name=f"sonarr:{sonarr_title}",
            category="sonarr",
            code=SONARR_TEMPLATE.format(title=sonarr_title),
        )
    )
    return steps


def _summarize_step_results(step_results: Iterable[StepResult]) -> Dict[str, Any]:
    rows = list(step_results)
    return {
        "stepCount": len(rows),
        "meanStepMs": statistics.fmean(row.elapsed_ms for row in rows) if rows else 0.0,
        "medianStepMs": statistics.median(row.elapsed_ms for row in rows) if rows else 0.0,
        "steps": [
            {
                "name": row.name,
                "category": row.category,
                "elapsedMs": row.elapsed_ms,
                "result": row.result,
            }
            for row in rows
        ],
    }


def run_media_household_benchmark(
    *,
    max_workers: int = 5,
    include_serial: bool = True,
    timeout_seconds: float = 30.0,
) -> Dict[str, Any]:
    steps = [ScenarioStep(name=s.name, category=s.category, code=s.code, timeout_seconds=timeout_seconds) for s in build_steps()]

    report: Dict[str, Any] = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "scenario": "media-household",
        "stepNames": [step.name for step in steps],
    }

    if include_serial:
        serial_started = time.perf_counter()
        serial_results = [_timed_run(step) for step in steps]
        report["serial"] = {
            "wallMs": (time.perf_counter() - serial_started) * 1000.0,
            **_summarize_step_results(serial_results),
        }

    parallel_started = time.perf_counter()
    parallel_results: List[StepResult] = []
    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(steps)))) as executor:
        futures = {executor.submit(_timed_run, step): step for step in steps}
        for future in as_completed(futures):
            parallel_results.append(future.result())
    report["parallel"] = {
        "maxWorkers": max_workers,
        "wallMs": (time.perf_counter() - parallel_started) * 1000.0,
        **_summarize_step_results(sorted(parallel_results, key=lambda item: item.name)),
    }
    return report


def default_output_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path('.omx') / 'benchmarks' / f'media-household-{timestamp}.json'


def write_report(report: Mapping[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')
    return output_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-workers', type=int, default=5)
    parser.add_argument('--parallel-only', action='store_true')
    parser.add_argument('--output', default=None)
    parser.add_argument('--timeout-seconds', type=float, default=30.0)
    args = parser.parse_args(argv)
    report = run_media_household_benchmark(max_workers=args.max_workers, include_serial=not args.parallel_only, timeout_seconds=args.timeout_seconds)
    output_path = Path(args.output) if args.output else default_output_path()
    write_report(report, output_path)
    print(output_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
