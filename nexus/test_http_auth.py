import asyncio
from typing import Any

from nexus.http_auth import NexusBearerVerifier, load_bearer_tokens_from_env


def test_verifier_accepts_configured_token() -> None:
    verifier = NexusBearerVerifier(["alpha"])

    token = asyncio.run(verifier.verify_token("alpha"))

    assert token is not None
    assert token.client_id.startswith("bearer-")
    assert token.token == "nexus-http-bearer"


def test_verifier_rejects_invalid_token_without_leaking_secret() -> None:
    verifier = NexusBearerVerifier(["secret-token"])

    token = asyncio.run(verifier.verify_token("wrong-token"))

    assert token is None
    assert "secret-token" not in repr(verifier)


def test_verifier_without_tokens_rejects_everything() -> None:
    verifier = NexusBearerVerifier([])

    assert verifier.has_tokens is False
    assert asyncio.run(verifier.verify_token("anything")) is None


def test_load_bearer_tokens_prefers_plural(monkeypatch: Any) -> None:
    monkeypatch.setenv("NEXUS_HTTP_BEARER_TOKEN", "single")
    monkeypatch.setenv("NEXUS_HTTP_BEARER_TOKENS", " alpha, beta ,, ")

    assert load_bearer_tokens_from_env() == ["alpha", "beta"]


def test_load_bearer_tokens_uses_singular_fallback(monkeypatch: Any) -> None:
    monkeypatch.delenv("NEXUS_HTTP_BEARER_TOKENS", raising=False)
    monkeypatch.setenv("NEXUS_HTTP_BEARER_TOKEN", "single")

    assert load_bearer_tokens_from_env() == ["single"]
