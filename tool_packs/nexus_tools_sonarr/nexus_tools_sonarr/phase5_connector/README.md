# Sonarr Phase 5 connector migration

This directory is the Sonarr-owned side of the Phase 5 native connector
contract. It is deliberately separate from the gateway worker implementation.

- `source.v1.json` preserves 222 current canonical identities, 14 aliases,
  original schemas, deterministic normalized migration evidence, and source
  digests. `@nexus/connector-sonarr` projects that evidence through the shared
  Phase 2 catalogue and Phase 5 connector contracts for the caller's exact
  Integration, Connection, and tenant scope.
- `reviewed_actions.py` is the exhaustive manual action review. Names, HTTP
  verbs, OpenAPI hints, and MCP annotations are not authorization inputs.
- `adapter.py` runs only in the connector boundary. The shared worker resolves
  Phase 3 SecretReference objects before calling its standard
  `factory(configuration, resolvedSecrets)` entrypoint. The adapter reuses one
  client per Connection and exposes the standard synchronous
  `invoke(operation, arguments, context)` contract.
- `build_source.py` is a deterministic migration exporter for the existing
  pack. It does not generate or rewrite Sonarr tools from OpenAPI.

Integration is the reusable `integration.sonarr` provider/schema. A Connection
is one named authenticated Sonarr instance. The TypeScript projector accepts
both explicitly and never hardcodes a home account. Authorization outcomes
remain exclusively in the core policy engine; reviewed pack metadata supplies
only exact-revision action classes.

Gateway integration must merge each descriptor's exact `actionMetadata` with
the action-scoped rules returned by `sonarrReviewedPolicyRules(manifest)` when
configuring `LocalSharedLifecycle`. Those defaults are inputs to the existing
core `PolicyEngine`; outer global, tenant, application, agent, and session rules
still combine by the engine's most-restrictive semantics. The connector adapter
must never evaluate or enforce a second policy path.

The `sonarr.list_season_releases` identity and behavior were migrated from the
protected current helper as read-only semantic input. The protected source and
test paths remain untouched; the connector implementation lives in
`phase5_connector/adapter.py`.
