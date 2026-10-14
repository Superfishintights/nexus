"""Bearer-token authentication for Nexus Streamable HTTP."""

from __future__ import annotations

import hashlib
import hmac

from fastmcp.server.auth import AccessToken, TokenVerifier

from nexus.env import get_setting


def _token_digest(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def load_bearer_tokens_from_env() -> list[str]:
    """Load configured bearer tokens without inventing defaults."""

    raw = get_setting(
        "NEXUS_HTTP_BEARER_TOKENS",
        "NEXUS_HTTP_BEARER_TOKEN",
    ) or ""
    return [token.strip() for token in raw.split(",") if token.strip()]


class NexusBearerVerifier(TokenVerifier):
    """FastMCP verifier backed by SHA-256 digests of configured tokens."""

    def __init__(self, tokens: list[str] | tuple[str, ...]) -> None:
        super().__init__()
        self._digest_hexes = tuple(
            hashlib.sha256(token.encode("utf-8")).hexdigest()
            for token in tokens
            if token
        )
        self._digests = tuple(bytes.fromhex(value) for value in self._digest_hexes)

    @property
    def has_tokens(self) -> bool:
        return bool(self._digests)

    async def verify_token(self, token: str) -> AccessToken | None:
        digest = _token_digest(token)
        matched = False
        digest_hex = hashlib.sha256(token.encode("utf-8")).hexdigest()
        for expected in self._digests:
            if hmac.compare_digest(digest, expected):
                matched = True
        if not matched:
            return None
        return AccessToken(
            token="nexus-http-bearer",
            client_id=f"bearer-{digest_hex[:16]}",
            scopes=[],
        )

    def client_fingerprint_for_token(self, token: str) -> str | None:
        digest_hex = hashlib.sha256(token.encode("utf-8")).hexdigest()
        for expected in self._digest_hexes:
            if hmac.compare_digest(digest_hex, expected):
                return digest_hex[:16]
        return None


def build_verifier_from_env() -> NexusBearerVerifier:
    return NexusBearerVerifier(load_bearer_tokens_from_env())
