# nexus_tools_bazarr

Nexus tool pack for the Bazarr API.

Configuration is read with `nexus.config.get_setting`:

- `BAZARR_URL`: Bazarr base URL, for example `http://localhost:6767`
- `BAZARR_API_KEY`: Bazarr API key sent as the `X-API-KEY` header
- `BAZARR_API_PATH`: optional API path override, defaults to `/api`
- `BAZARR_TIMEOUT_S`: optional request timeout in seconds, defaults to `30.0`

Generated tools use the `bazarr` namespace and mirror every operation in the Swagger 2.0 source spec. Query parameters are passed through the generic `params` mapping. POST/PATCH body payloads are passed through `body`.

Multipart upload endpoints accept a body shaped like:

```python
load_tool("bazarr.create_movies_subtitles")(
    params={"radarrid": 1, "language": "en", "forced": "False", "hi": "False"},
    body={"file": "/path/to/subtitles.srt"},
)
```

Install with:

```bash
pip install -e .
```

Then add this package root to `NEXUS_TOOL_PACKAGES`.
