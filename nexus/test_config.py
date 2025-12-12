import os
from pathlib import Path

from nexus.config import get_setting


def test_get_setting_reads_env_file_and_refreshes(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TAUTULLI_URL", raising=False)
    env_file = tmp_path / "nexus.env"
    monkeypatch.setenv("NEXUS_ENV_FILE", str(env_file))

    env_file.write_text("TAUTULLI_URL=https://example\n", encoding="utf-8")
    assert get_setting("TAUTULLI_URL") == "https://example"

    before = env_file.stat().st_mtime
    env_file.write_text("TAUTULLI_URL=https://changed\n", encoding="utf-8")
    os.utime(env_file, (before + 5, before + 5))

    assert get_setting("TAUTULLI_URL") == "https://changed"


def test_get_setting_env_overrides_file(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / "nexus.env"
    monkeypatch.setenv("NEXUS_ENV_FILE", str(env_file))
    env_file.write_text("TAUTULLI_URL=https://file\n", encoding="utf-8")

    monkeypatch.setenv("TAUTULLI_URL", "https://env")
    assert get_setting("TAUTULLI_URL") == "https://env"
