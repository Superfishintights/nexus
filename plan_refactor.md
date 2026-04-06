# Nexus Refactor Plan

This document is the implementation plan for a fresh session.

This is a refactor, not a rewrite.

The core problem has two parts:

- distribution: users should only install the tool packs they actually want
- authorization: restricted agents should only be able to discover and use the tools they are explicitly allowed to use

A simple split between `nexus/` and `tools/` helps distribution, but it does not solve authorization by itself.

## Target Outcome

Move the project toward this shape:

```text
NEXUS_PROJECT/
  nexus/                       # core runtime package
  tool_packs/
    nexus_tools_jira/
    nexus_tools_n8n/
    nexus_tools_sonarr/
    nexus_tools_radarr/
    nexus_tools_tautulli/
    nexus_tools_starling/
```

Then publish multiple installable packages:

- `nexus-core`
- `nexus-tools-jira`
- `nexus-tools-n8n`
- `nexus-tools-sonarr`
- `nexus-tools-radarr`
- `nexus-tools-tautulli`
- `nexus-tools-starling`
- optional convenience packages later, such as `nexus-tools-media`

The recommended model is:

- one monorepo for development
- multiple installable packages for distribution
- one distinct Python import root per published tool pack
- optional later move to multiple GitHub repos only if ownership or release cadence requires it

Important packaging decision:

- do not publish multiple distributions that all contribute to the same regular top-level `tools` package
- either use namespace packaging deliberately or, preferably for v1, give each published pack its own import root such as `nexus_tools_jira`
- `NEXUS_TOOL_PACKAGES` should point at those package roots

## Why This Refactor Exists

The current setup is too coarse.

- A user who only wants `n8n` should not need to ship media and banking tooling.
- A home Plex agent should not inherit every tool in `sonarr`, `radarr`, or unrelated namespaces.
- A work environment should not need personal integrations.
- A safety-sensitive agent needs real runtime enforcement, not filtered discovery output.

## Current Friction Points

These files currently encode the monolithic assumption or are the future enforcement points:

- `README.md`
- `tools/README.md`
- `nexus/pyproject.toml`
- `nexus/selftest.py`
- `DIST.md`
- `BUNDLE.md`
- `scripts/build_nexus_bundle.py`
- `nexus/tool_catalog.py`
- `nexus/lazy_tools.py`
- `nexus/tool_registry.py`
- `nexus/runner.py`
- `nexus/execution_worker.py`
- `nexus/server.py`
- `nexus/config.py`
- `nexus/settings/runner.py`
- `nexus/test_tool_catalog.py`
- `nexus/test_lazy_tools.py`

Important observations from the current code:

- packaging currently includes `tools*` from the runtime package metadata
- self-test currently assumes `tools` is always present
- tool discovery defaults to a global `tools` package
- runtime access control does not exist yet
- `run_code` still exposes `__import__`, so discovery filtering is not a security boundary
- aliases are hidden from default discovery, but are still directly loadable
- tool metadata does not capture installable-package provenance, only tool name and module path
- core config and `RUNNER_SETTINGS` still import service-specific settings modules
- `tools/__init__.py` makes `tools` a regular package, so splitting it across multiple published distributions would be fragile or impossible without a packaging change

## Working Model For The Fresh Session

The next session should use roles deliberately.

### Main Agent Responsibilities

The main agent must own:

- final package boundary decisions
- final import-root and migration strategy
- final policy model design
- security-sensitive choices
- any decision that changes user-facing behavior
- final code review and end-to-end verification

### Explorer Subagent Responsibilities

Explorer subagents should only be used for exploration-style tasks such as:

- locating coupling points
- finding every enforcement path
- reviewing test and doc fallout
- checking generated tool-tree implications
- mapping service-specific settings still living under core
- enumerating legacy alias usage that affects migration

Explorer subagents should not be used for final architecture decisions or policy semantics.

### Worker Responsibilities

Worker should only be used for basic or mechanical coding tasks such as:

- scaffolding package metadata
- moving files once the target structure is decided
- repetitive doc updates
- repetitive test edits
- boilerplate policy plumbing after the main agent has defined the design

## Recommended Architecture Decisions

These should be treated as the default design unless the fresh session finds a hard blocker.

### 1. Keep A Monorepo

Start with one repo.

Do not split into multiple GitHub repos yet.

Reason:

- lower coordination cost
- easier refactor and testing
- easier shared versioning while the design is still changing

### 2. Publish Multiple Packages With Distinct Import Roots

Do not publish one giant `tools` package as the primary install surface.

The normal user choice should be:

- install `nexus-core`
- install only the tool packs they need

The published packs should not share one regular top-level Python package.

Good:

- import roots such as `nexus_tools_jira`, `nexus_tools_n8n`, `nexus_tools_sonarr`
- `NEXUS_TOOL_PACKAGES=nexus_tools_jira,nexus_tools_n8n`

Bad:

- multiple pip distributions all writing into `tools.*`
- package splits that still require `nexus-core` to ship the first-party tool tree

### 3. Use Integration-Level Tool Packs

The right install unit is usually the integration or domain family, not the individual function.

Good:

- `nexus-tools-sonarr`
- `nexus-tools-radarr`
- `nexus-tools-tautulli`
- `nexus-tools-n8n`

Bad:

- one package containing every tool for every domain
- one package per individual function

### 4. Use Canonical Tool IDs As The Only Policy Surface In Restricted Mode

Restricted mode should operate on canonical tool names only.

Canonical policy surface:

- canonical tool name, for example `jira.get_issue_status`
- namespace, for example `jira`
- class, for example `read` or `destructive`

Alias policy surface:

- none in restricted mode

Implications:

- aliases may remain as unrestricted backwards compatibility only
- restricted profiles should not rely on legacy names
- policy checks should resolve to canonical tool IDs before evaluation

### 5. Add A First-Class Tool Policy

Policy must become an explicit runtime concept.

Recommended v1 fields:

- `name`
- `mode` such as `unrestricted` or `restricted`
- `allowed_namespaces`
- `allowed_tools`
- `denied_tools`
- `allowed_classes`
- `denied_classes`

Do not include `allowed_packages` in v1.

Reason:

- the current metadata does not reliably know which installable distribution owns a tool
- package-level policy should wait until the runtime tracks real provenance instead of guessing from module paths

Suggested precedence:

1. explicit deny
2. explicit tool allow
3. class allow
4. namespace allow
5. default deny for restricted profiles

### 6. Restricted Mode Must Be A Genuine Tool-Authorization Boundary

Restricted mode should be designed as real authorization for registered tool use, not just a safer UX.

This means:

- restricted mode must not rely on discovery filtering alone
- restricted mode must not expose arbitrary `__import__`
- restricted mode must block direct imports of tool-pack modules as a bypass
- restricted mode must enforce policy consistently in `search_tools`, `get_tool`, `TOOLS`, and `load_tool`

Important scope limit:

- this is a genuine authorization boundary for registered Nexus tools
- this is not the same as claiming a full Python, OS, filesystem, or network sandbox

### 7. Add Tool Safety Classes

Namespace-only filtering is too coarse.

Introduce tool classes such as:

- `read`
- `write`
- `admin`
- `destructive`

This supports cases like:

- allow `sonarr.*`
- allow classes `read` and `write`
- deny class `destructive`
- deny a specific dangerous tool explicitly

### 8. Keep Policy Selection Server-Wide In V1

V1 should choose policy at the server instance level, not per MCP call.

Reason:

- the current MCP surface is stateless
- per-session or per-call policy introduces a larger API and lifecycle design problem
- server-wide policy is enough to validate the boundary first

## Phased Plan

Each phase below includes ownership guidance.

### Phase 0: Lock The Decisions

Objective:

- confirm the target package model
- confirm the import-root strategy
- confirm the canonical-only policy model
- confirm that restricted mode is intended as a real tool-authorization boundary

Main agent:

- decide final package names
- decide the target source layout for pack roots
- decide how legacy `tools.*` imports migrate
- decide whether aliases remain available only in unrestricted mode or are removed entirely
- decide policy precedence rules
- decide the exact restricted execution model for v1

Explorer subagents:

- verify remaining coupling points
- enumerate service-specific settings that weaken a pure-core package
- enumerate destructive tools that should later receive safety classes
- locate code paths that currently rely on alias names

Worker:

- none

Deliverable:

- agreed architecture in session before code motion starts

### Phase 1: Separate Core From Tool Packs At The Packaging And Runtime Level

Objective:

- make `nexus-core` install and run with zero tool packs present
- move first-party tool packs to distinct import roots
- remove core imports that drag pack-specific settings into the runtime

Main agent:

- decide exact monorepo layout
- decide whether temporary compatibility shims are needed for `tools.*`
- decide what remains in `nexus-core`

Explorer subagents:

- inspect all build, doc, bundle, and self-test assumptions that rely on local `tools`
- inspect pack code for intra-package imports that assume `tools.<service>`

Worker:

- scaffold package metadata
- update install docs once the shape is decided
- perform low-risk file moves
- update self-test and bundle docs after the runtime shape is settled

Likely files to touch:

- `nexus/pyproject.toml`
- `README.md`
- `tools/README.md`
- `nexus/selftest.py`
- `DIST.md`
- `BUNDLE.md`
- `scripts/build_nexus_bundle.py`
- `nexus/config.py`
- `nexus/settings/runner.py`

Acceptance criteria:

- core runtime installs and runs without the whole tool tree
- core default behavior with no tool packs present is explicit and warning-free
- selected tool packs can be installed independently
- no published-pack design depends on multiple distributions sharing one regular `tools` package

### Phase 2: Introduce Canonical-Only Tool Policy As A Runtime Primitive

Objective:

- make allowed tools explicit and testable
- make canonical tool identity the only restricted-mode policy surface

Main agent:

- define the `ToolPolicy` API
- define unrestricted vs restricted behavior
- define canonical-name resolution rules
- define how aliases behave in unrestricted mode

Explorer subagents:

- verify every code path that can leak, load, or expose tool metadata
- verify every path where alias names still enter the system

Worker:

- create the policy module and mechanical plumbing once the main agent defines it

Likely files to touch:

- `nexus/tool_catalog.py`
- `nexus/lazy_tools.py`
- `nexus/tool_registry.py`
- `nexus/runner.py`
- `nexus/server.py`

Acceptance criteria:

- `search_tools` respects policy
- `get_tool` respects policy
- `TOOLS` respects policy
- `load_tool` refuses disallowed tools
- restricted mode operates on canonical names only

### Phase 3: Restricted Execution Hardening

Objective:

- make restricted mode a genuine authorization boundary for registered tool use

Important release rule:

- restricted mode should not ship publicly until this phase and Phase 2 are both complete

Main agent:

- decide whether restricted mode uses separate execution globals, a separate worker mode, or both
- decide which builtins remain available in restricted mode
- decide whether unrestricted mode keeps direct imports for trusted environments

Explorer subagents:

- review bypass paths through `run_code`
- identify what remains reachable with current builtins/imports
- identify direct import paths into tool-pack modules

Worker:

- implement mechanical runner changes after decisions are made

Likely files to touch:

- `nexus/runner.py`
- `nexus/execution_worker.py`
- `nexus/server.py`

Acceptance criteria:

- restricted mode does not expose arbitrary `__import__`
- restricted mode cannot bypass policy by importing tool-pack modules directly
- the team is explicit about what restricted mode does and does not protect against

### Phase 4: Add Safety Classes To Tools

Objective:

- make safe profiles practical without hand-curating everything forever

Main agent:

- define class semantics
- decide whether classes live in `@register_tool(...)` metadata or an external manifest

Explorer subagents:

- identify destructive and high-risk tools in large namespaces
- propose initial class assignments for generated packs

Worker:

- add metadata to many tool definitions once the schema is fixed

Likely files to touch:

- tool registration metadata in tool packs
- possibly `nexus/tool_registry.py`
- possibly `nexus/tool_catalog.py`

Acceptance criteria:

- profiles can express "allow namespace but deny destructive/admin"

### Phase 5: Presets And Install Profiles

Objective:

- make the public install story and policy story obvious

Suggested install profiles:

- `media`: Sonarr, Radarr, Tautulli
- `work-n8n`: n8n only
- `personal-admin`: full trusted setup

Suggested policy presets:

- `unrestricted`
- `plex-readonly`
- `plex-safe-write`
- `work-n8n`
- `personal-admin`

Main agent:

- define which presets are officially supported

Explorer subagents:

- audit whether preset names and boundaries match real user scenarios

Worker:

- add preset docs and configuration examples

## Open Design Questions To Resolve In The Fresh Session

The key decisions above are locked. The remaining open questions are implementation details:

- What temporary migration path should exist from `tools.*` imports to pack-specific import roots?
- Should unrestricted mode keep legacy aliases for one transition period, or should aliases be removed entirely once canonical names are in place?
- Should safety classes be stored in decorator metadata, a manifest, or both?
- Should curated meta-packages exist in v1, or wait until the package split is stable?
- Should pack-specific typed settings live inside each tool pack, or should some remain as optional extension modules adjacent to core?

## Validation Plan

Minimum validation needed before calling the refactor successful:

- unit tests for core empty-catalog behavior with no tool packs installed
- unit tests for policy filtering in catalog search
- unit tests for `get_tool` under allowlist and denylist scenarios
- unit tests for `TOOLS` visibility under restricted profiles
- unit tests for `load_tool` refusal on disallowed tools
- unit tests for canonical-name enforcement in restricted mode
- unit tests proving alias names are rejected in restricted mode
- unit tests proving restricted mode cannot import tool-pack modules directly
- smoke test that unrestricted mode behaves like today where compatibility is intentionally preserved
- smoke test that a restricted profile only sees and loads allowed tools
- install test that core works without unrelated tool packs present

Likely tests to revisit:

- `nexus/test_tool_catalog.py`
- `nexus/test_lazy_tools.py`
- `nexus/test_runner.py`
- `nexus/selftest.py`

## Non-Goals

- do not split into one repo per individual function
- do not publish one giant first-party `tools` blob as the only install option
- do not rely on discovery filtering alone for safety
- do not ship restricted mode before execution hardening is complete
- do not claim a full Python, OS, or network sandbox unless that is actually implemented
- do not introduce package-level policy in v1 without real package provenance metadata

## Implementation Order Summary

The fresh session should execute in this order:

1. main agent confirms final package, import-root, and restricted-mode design
2. explorer subagents verify coupling points, alias fallout, and safety-sensitive surfaces
3. worker handles package scaffolding and mechanical file moves
4. main agent implements the restricted execution boundary and canonical policy surface
5. worker handles repetitive follow-up edits and metadata rollout
6. main agent runs final verification and writes the final summary

## Decision Summary

The recommended path is:

1. keep one monorepo for now
2. split distribution into `nexus-core` plus per-integration tool packs with distinct import roots
3. use canonical tool IDs only in restricted mode
4. add a first-class runtime policy based on namespaces, explicit tools, and safety classes
5. make restricted mode a genuine authorization boundary for registered Nexus tools
6. treat package-level policy as a later enhancement after provenance metadata exists
