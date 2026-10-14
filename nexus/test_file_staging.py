from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import pytest

from nexus.file_staging import (
    FileStagingConfig,
    FileStagingService,
    _safe_filename,
    load_file_staging_config,
)
from nexus.http_auth import NexusBearerVerifier


def test_safe_filename_rejects_paths_and_honours_extension_policy() -> None:
    with pytest.raises(ValueError, match="invalid_filename"):
        _safe_filename("..%2Freport.html")
    with pytest.raises(ValueError, match="invalid_filename"):
        _safe_filename("folder%5Creport.html")
    with pytest.raises(ValueError, match="extension_not_allowed"):
        _safe_filename("report.html", allowed_extensions=frozenset({".pdf"}))

    assert _safe_filename("Résumé%20final.html") == "R_sum_ final.html"


def test_custom_extension_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_file = tmp_path / "empty.env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("NEXUS_ENV_FILE", str(env_file))
    monkeypatch.setenv("NEXUS_FILE_STAGING_ROOT", str(tmp_path / "staged"))
    monkeypatch.setenv("NEXUS_FILE_STAGING_ALLOWED_EXTENSIONS", "html,.custom")

    config = load_file_staging_config()

    assert config is not None
    assert config.allowed_extensions == frozenset({".html", ".custom"})


def test_staging_root_must_be_absolute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_file = tmp_path / "empty.env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("NEXUS_ENV_FILE", str(env_file))
    monkeypatch.setenv("NEXUS_FILE_STAGING_ROOT", "relative/staged")

    with pytest.raises(RuntimeError, match="absolute path"):
        load_file_staging_config()


def test_cleanup_removes_expired_artifact_but_never_external_path(tmp_path: Path) -> None:
    root = tmp_path / "staged"
    client_dir = root / "client"
    meta_dir = client_dir / "metadata"
    meta_dir.mkdir(parents=True)
    expired = client_dir / ("a" * 32 + ".html")
    expired.write_text("expired", encoding="utf-8")
    external = tmp_path / "external.txt"
    external.write_text("keep", encoding="utf-8")
    stale_tmp = client_dir / ".stale.tmp"
    stale_tmp.write_text("partial", encoding="utf-8")
    old_time = time.time() - 2 * 24 * 60 * 60
    stale_tmp.touch()
    stale_tmp.chmod(0o600)
    os.utime(stale_tmp, (old_time, old_time))
    expired_meta = meta_dir / ("a" * 32 + ".json")
    external_meta = meta_dir / ("b" * 32 + ".json")
    expired_meta.write_text(
        json.dumps({"path": str(expired), "expires_at_epoch": time.time() - 1}),
        encoding="utf-8",
    )
    external_meta.write_text(
        json.dumps({"path": str(external), "expires_at_epoch": time.time() - 1}),
        encoding="utf-8",
    )
    service = FileStagingService(
        FileStagingConfig(root=root),
        NexusBearerVerifier(["alpha"]),
    )

    asyncio.run(service.cleanup_expired())

    assert not expired.exists()
    assert not expired_meta.exists()
    assert external.read_text(encoding="utf-8") == "keep"
    assert not external_meta.exists()
    assert not stale_tmp.exists()


def test_cleanup_removes_old_orphaned_temp_files(tmp_path: Path) -> None:
    root = tmp_path / "staged"
    client_dir = root / "client"
    meta_dir = client_dir / "metadata"
    meta_dir.mkdir(parents=True)
    old_tmp = client_dir / ".old.tmp"
    old_meta_tmp = meta_dir / ".old.json.tmp"
    fresh_tmp = client_dir / ".fresh.tmp"
    old_tmp.write_text("old", encoding="utf-8")
    old_meta_tmp.write_text("old-meta", encoding="utf-8")
    fresh_tmp.write_text("fresh", encoding="utf-8")
    old_time = time.time() - 120
    fresh_time = time.time()
    os.utime(old_tmp, (old_time, old_time))
    os.utime(old_meta_tmp, (old_time, old_time))
    os.utime(fresh_tmp, (fresh_time, fresh_time))
    service = FileStagingService(
        FileStagingConfig(root=root, ttl_seconds=60),
        NexusBearerVerifier(["alpha"]),
    )

    asyncio.run(service.cleanup_expired())

    assert not old_tmp.exists()
    assert not old_meta_tmp.exists()
    assert fresh_tmp.exists()


def test_cleanup_keeps_unexpired_artifact(tmp_path: Path) -> None:
    root = tmp_path / "staged"
    client_dir = root / "client"
    meta_dir = client_dir / "metadata"
    meta_dir.mkdir(parents=True)
    artifact = client_dir / ("c" * 32 + ".txt")
    artifact.write_text("keep", encoding="utf-8")
    metadata = meta_dir / ("c" * 32 + ".json")
    metadata.write_text(
        json.dumps({"path": str(artifact), "expires_at_epoch": time.time() + 60}),
        encoding="utf-8",
    )
    service = FileStagingService(
        FileStagingConfig(root=root),
        NexusBearerVerifier(["alpha"]),
    )

    asyncio.run(service.cleanup_expired())

    assert artifact.read_text(encoding="utf-8") == "keep"
    assert metadata.exists()


def test_start_rejects_symlink_root(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    service = FileStagingService(
        FileStagingConfig(root=link),
        NexusBearerVerifier(["alpha"]),
    )

    with pytest.raises(RuntimeError, match="must not be a symlink"):
        service.start()
