# nexus_tools_google_common

Shared standard-library Google OAuth and HTTP client support for Nexus Google tool packs.

This package intentionally registers no Nexus tools. App-specific packs import the shared client and expose their own `@register_tool` functions.

## Configuration

- `GOOGLE_ACCESS_TOKEN`: short-lived bearer token override.
- `GOOGLE_REFRESH_TOKEN`: refresh token for normal operation.
- `GOOGLE_CLIENT_ID`: OAuth client ID.
- `GOOGLE_CLIENT_SECRET`: OAuth client secret, optional for installed-app PKCE clients.
- `GOOGLE_CLIENT_CONFIG_FILE`: Google desktop OAuth client JSON path. Values under `installed.client_id`, `installed.client_secret`, `installed.auth_uri`, `installed.token_uri`, and `installed.redirect_uris` are used when the matching explicit env var is absent.
- `GOOGLE_AUTH_URL`: defaults to `https://accounts.google.com/o/oauth2/v2/auth`.
- `GOOGLE_TOKEN_URL`: defaults to `https://oauth2.googleapis.com/token`.
- `GOOGLE_REDIRECT_URI`: redirect URI for manual code exchange.
- `GOOGLE_SCOPES`: space- or comma-separated OAuth scopes for helper flows.
- `GOOGLE_TOKEN_FILE`: token JSON path, default `~/.config/nexus/google-token.json`.
- `GOOGLE_TIMEOUT_SECONDS`: request timeout, default `30`.
- `GOOGLE_RETRY_COUNT`: retry count, default `2`.
- `GOOGLE_RETRY_BASE_SECONDS`: exponential retry base delay, default `0.5`.

Token files are written with `0600` permissions and parent directories are set to `0700`. Existing token files and client config files with group or world permissions are rejected.

## Public API

```python
from nexus_tools_google_common import (
    GoogleApiClient,
    GoogleApiError,
    GoogleAuthError,
    GoogleResponse,
    build_authorization_url,
    coerce_json,
    coerce_list,
    exchange_authorization_code,
    exchange_authorization_redirect,
    get_client,
    quote_path_segment,
    quote_resource_name,
    run_loopback_authorization,
)
```

Supported service keys:

- `calendar`
- `gmail`
- `drive`
- `drive_upload`
- `docs`
- `sheets`
- `slides`
- `people`
- `tasks`
- `forms`
- `script`

`GoogleApiClient.request(...)` supports JSON payloads, raw byte/string bodies, binary responses, multipart media upload, resumable upload session creation, response headers, OAuth refresh-on-401, and normalized Google API errors.

## OAuth

For manual setup, generate an authorization URL:

```python
auth = build_authorization_url(scopes="https://www.googleapis.com/auth/drive")
print(auth["url"])
```

After completing consent, pass the complete returned redirect URL so its OAuth
state is verified before the code is exchanged:

```python
exchange_authorization_redirect(
    redirect_url,
    expected_state=auth["state"],
    code_verifier=auth["code_verifier"],
)
```

For local loopback flow:

```python
run_loopback_authorization(scopes=["https://www.googleapis.com/auth/calendar"], open_browser=True)
```

The loopback server binds only to `127.0.0.1`.
