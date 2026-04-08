from pathlib import Path

from nexus.benchmark_phase1 import BenchmarkCase, benchmark_case, summarize_samples, write_report


def test_summarize_samples_reports_basic_stats() -> None:
    summary = summarize_samples([1.0, 2.0, 3.0])

    assert summary == {
        "iterations": 3,
        "minMs": 1.0,
        "maxMs": 3.0,
        "meanMs": 2.0,
        "medianMs": 2.0,
    }


def test_benchmark_case_captures_iterations() -> None:
    counter = {"count": 0}

    def run() -> dict[str, int]:
        counter["count"] += 1
        return counter

    result = benchmark_case(
        BenchmarkCase(
            name="demo",
            category="runner",
            detail="demo case",
            call=run,
        ),
        iterations=3,
        warmups=2,
    )

    assert result["name"] == "demo"
    assert result["iterations"] == 3
    assert len(result["latenciesMs"]) == 3
    assert counter["count"] == 5


def test_write_report_creates_parent_dirs(tmp_path: Path) -> None:
    output_path = tmp_path / "benchmarks" / "phase1.json"
    written = write_report({"cases": []}, output_path)

    assert written == output_path
    assert output_path.exists()
    assert '"cases": []' in output_path.read_text(encoding="utf-8")
