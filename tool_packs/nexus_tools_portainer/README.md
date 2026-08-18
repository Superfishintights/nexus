# nexus_tools_portainer

Focused Nexus tool pack for Portainer status checks and Docker container control.

This pack intentionally does not wrap the full Portainer API. It covers the practical
surface needed to find Portainer environments, locate Plex/media containers, inspect
container state, and start/stop/restart containers through Portainer's Docker proxy.

## Settings

Required:

- `PORTAINER_URL`: Base Portainer URL. The client adds `https://` when no scheme is present.

Authentication, in priority order:

- `PORTAINER_API_KEY`: Sent as `X-API-KEY`.
- `PORTAINER_JWT` or `PORTAINER_TOKEN`: Sent as `Authorization: Bearer ...`.
- `PORTAINER_USERNAME` and `PORTAINER_PASSWORD`: Used to call `/auth` and cache the returned JWT in process.

Optional:

- `PORTAINER_TIMEOUT_S`: Request timeout in seconds. Defaults to `30`.

## Scope

Included tools:

- Server health/status/version: cheap readiness checks.
- Environment listing and lookup: needed to pick the Docker endpoint.
- Container list/search/inspect/status: needed to find Plex/media services and verify state.
- Container start/stop/restart: the focused control surface requested for the Plex server.

Stack/service controls are intentionally left out for now. They are useful in some Portainer
setups, but container control is the shared denominator for Plex/media service recovery and
keeps this pack small enough to validate without live Portainer access.

## Install

```bash
pip install -e .
```

Then include `nexus_tools_portainer` in `NEXUS_TOOL_PACKAGES`.
