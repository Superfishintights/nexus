from pathlib import Path

from nexus.benchmark_report import render_markdown_report, summarize_comparison, write_markdown_report


def test_summarize_comparison_computes_improvement() -> None:
    summary = summarize_comparison(
        {
            "oneshot": {"cases": [{"name": "run_code:trivial", "meanMs": 100.0}]},
            "persistent": {"cases": [{"name": "run_code:trivial", "meanMs": 25.0}]},
        },
        baseline_label="oneshot",
        focus_label="persistent",
        case_names=("run_code:trivial",),
    )

    assert round(summary["run_code:trivial"]["persistent_vs_oneshot_pct"], 1) == 75.0


def test_render_markdown_report_includes_rows() -> None:
    markdown = render_markdown_report(
        {
            "run_code:trivial": {
                "oneshot": 100.0,
                "persistent": 25.0,
                "persistent_vs_oneshot_pct": 75.0,
            }
        },
        baseline_label="oneshot",
        focus_label="persistent",
    )

    assert "Nexus benchmark comparison" in markdown
    assert "run_code:trivial" in markdown
    assert "75.0%" in markdown


def test_write_markdown_report_creates_file(tmp_path: Path) -> None:
    output = tmp_path / "benchmarks" / "report.md"
    written = write_markdown_report("# demo\n", output)

    assert written == output
    assert output.read_text(encoding="utf-8") == "# demo\n"
