# nexus_tools_qbittorrent

Nexus tool pack for the qBittorrent WebUI API v5.0 documentation.

Configuration is read through `nexus.config.get_setting`:

- `QBITTORRENT_URL`
- `QBITTORRENT_USERNAME`
- `QBITTORRENT_PASSWORD`
- `QBITTORRENT_TIMEOUT_S` optional, default `30`
- `QBITTORRENT_API_PATH` optional, default `/api/v2`

Install with:

```bash
pip install -e .
```

Then add this package root to `NEXUS_TOOL_PACKAGES`.

```bash
export NEXUS_TOOL_PACKAGES="nexus_tools_qbittorrent"
```

The client uses qBittorrent's cookie-based WebUI authentication and logs in lazily before authenticated requests. Tests do not require a live qBittorrent server.
