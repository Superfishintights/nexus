# Running source snapshot

Captured on 14 October 2026 from the active Python Streamable HTTP service. The source image digest was `sha256:7f68f96b5134a046a30db5ad0ed5b2117044031e29bfebb478dd4fee6a920267`.

The core source comes from the imported `/app/nexus` package. Tool-pack source comes from the imported installed packages, rather than potentially stale image build directories. Build metadata and offline tests accompany those packages.

The runtime selects 30 active namespaces, with 2,177 discoverable canonical operations and 2,249 dispatch names including compatibility aliases. Chaptarr contributes 318 operations. Retired Blackboard source is optional and disabled by default.

No deployment secrets, OAuth token files, user state, message records, uploads or local environment files were copied. Repository privacy checks cover the assembled tree and existing GitHub history. Any publication-only metadata sanitation is documented here.

Synchronizing source does not restart or replace the running service. Build and smoke-test evidence is recorded below after validation.

## Publication changes

Private generated provenance paths and deployment addresses in documentation/spec server metadata use generic examples. Playtomic's hardcoded private ntfy destination was replaced with the `PLAYTOMIC_NTFY_TOPIC` setting. Notifications require that setting in deployments built from this source. All operation names and aliases are preserved. Test assertions for the complete monorepo are maintained separately from runtime source.

Docker build networking uses the host network on Linux to match the service build setup. This avoids the local Docker bridge DNS failure observed during verification.

## Verification

The standalone Docker image built successfully from this repository. Its catalog matches the running service exactly, with no missing or extra dispatch names and no catalog problems. An isolated HTTP smoke check confirmed healthy startup, rejection of unauthenticated MCP calls, the four gateway tools, all 30 namespaces, and code execution returning the expected result.

Gitleaks 8.30.1 found no secrets in the assembled tree or the reachable history of either previously published branch. A separate private-data scan found no personal home paths, private deployment hostnames, private key blocks or real credential files. Network-safety tests retain synthetic local-network addresses. Pattern-based scans cannot prove absence of every possible secret.

The supported offline suite passed all 1,018 tests. It covers the core, HTTP/authentication/file staging, active tool-pack contracts and the configurable Playtomic notification destination. Retired Blackboard tests and the historical Sonarr/Memory Phase 5 connector suites are excluded because they belong to different release work and can rewrite source manifests. The command is in the root README. No live provider writes were used for validation.
