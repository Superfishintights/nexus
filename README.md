# Nexus

Nexus is a Python MCP gateway with independently installable tool packs. The default branch contains the source used by the running Streamable HTTP service, including its authentication, file staging, tool discovery and execution workers.

The gateway exposes `run_code`, `search_tools`, `get_tool` and `list_tool_namespaces`. Tool operations remain behind the gateway, so clients can discover the operations they need without loading the whole catalog.

## Run with Docker

The repository contains the core and all tool-pack sources. No sibling repositories or prebuilt overlay images are required.

```sh
cp .env.example .env
mkdir -p secrets state uploads staged-files
# Edit .env with your own token, endpoints and service credentials.
docker compose build
docker compose up -d
```

Compose binds to localhost by default. Change the published address for your own network or reverse proxy. The MCP endpoint is `/mcp`; health checks use `/healthz`. A configured bearer token is required. Store credentials in the excluded `.env` file and `secrets/` directory, never in Git.

The Docker image selects 30 active tool packs. Shared Google helpers and the retired Blackboard pack are available in the source tree; Blackboard is not enabled in the default runtime. See [the source snapshot](docs/running-source.md) for catalog counts and validation.

## Discover and call tools

Use `search_tools` and `get_tool` to inspect operations, or enumerate the lazy `TOOLS` catalog inside `run_code`.

```python
RESULT = load_tool("waha.get_health")()
```

Each tool pack under `tool_packs/` has its own package metadata and configuration. Install only the packs needed for a smaller deployment. The core also supports stdio through `python -m nexus.server`.

## Local installation and checks

```sh
python3 -m venv .venv
.venv/bin/pip install -c requirements-runtime.txt './nexus[test]' ./tool_packs/nexus_tools_*
.venv/bin/python -m nexus.selftest
env -u NEXUS_TOOL_PACKAGES PYTHONPATH="$PWD" .venv/bin/python -m pytest nexus tool_packs --import-mode=importlib \
  --ignore-glob='*/phase5_tests/*' --ignore-glob='*/nexus_tools_agent_blackboard/*'
```

The supported offline suite excludes the retired Blackboard pack and historical Phase 5 connector tests. Those tests belong to separate unreleased work and can regenerate source manifests. Some optional integration tests require separately configured services. The runtime dependency constraints record the versions in the source service at synchronization time.

## Private data

Provider keys, OAuth tokens, account state, uploads and credentials are deployment data. They are excluded from Git and the Docker build context. Examples and unit tests must use synthetic values. This repository does not contain the running service's environment or mounted secret/state directories.
