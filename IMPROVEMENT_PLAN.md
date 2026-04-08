# Improvement Plan

## Decision Summary

Nexus should improve as a **brownfield agent runtime** built from the
code that already exists, not as a speculative rewrite or a broader
product/platform project.

This plan is Linux-first, keeps later Mac portability in view, and
frames language/runtime changes as **evidence-gated decisions** rather
than assumed upgrades.

Default decision rule:

- **Keep Python unless evidence proves a materially better path.**
- Treat alternate runtimes, supervisors, and broader platform expansion
  as follow-on options, not default roadmap commitments.
- Treat **minimal change or no major rewrite** as a valid outcome if the
  evidence shows the current architecture is already good enough.

## What This Plan Is Optimizing For

Prioritize changes only when they produce meaningful gains in one or
more of these areas:

- runtime speed and latency,
- agent accuracy and tool-use reliability,
- sandboxing and safety,
- runtime extensibility that improves Nexus itself,
- deployment and operational simplicity.

## Brownfield Grounding

Nexus is not starting from zero. The repository already contains the
main primitives this effort is about:

- `nexus/server.py` exposes the narrow MCP surface: `run_code`,
  `search_tools`, and `get_tool`
- `nexus/runner.py` already executes model-authored Python and exposes
  `TOOLS` / `load_tool(...)`
- `nexus/execution_worker.py` already provides subprocess execution
  scaffolding
- `nexus/tool_policy.py` already implements unrestricted/restricted
  policy concepts and named presets

Because these primitives already exist, the strongest near-term
opportunity is **not** “pick a new language.” The strongest near-term
opportunity is to:

1. measure the current runtime,
2. tighten the host/runner boundary,
3. validate a restricted runtime that still supports legitimate tool
   usage,
4. only then decide whether deeper runtime changes are justified.

## Primary Code Touchpoints

Later execution or review work should stay grounded in these files:

- `nexus/server.py` — public MCP boundary and current tool-discovery /
  tool-metadata surface
- `nexus/runner.py` — execution globals, lazy tool loading, limits, and
  runner behavior
- `nexus/execution_worker.py` — subprocess execution boundary for
  bounded runs
- `nexus/tool_policy.py` — policy modes, presets, authorization
  semantics, and restricted-mode expectations

If a proposed roadmap change does not clearly relate back to one or more
of these touchpoints, it is too speculative for the current phase.

## Verification Path For The Next Execution Lane

Any follow-on implementation or review should verify the plan against
these checkpoints:

- benchmark/eval artifacts must show the actual bottleneck before
  optimization work is prioritized
- host/runner boundary proposals must map back to `server.py`,
  `runner.py`, `execution_worker.py`, and `tool_policy.py`
- restricted-runtime validation must prove blocked shell/network/
  filesystem behavior **and** preserved host-mediated tool access
- proposed phase work must explicitly avoid reintroducing web UI,
  cloud/shared deployment, Rust, dynamic tool creation, or broad CLI
  execution into the current phase
- proposed execution plans should cite which verification checkpoint or
  measured result justifies the work before expanding scope
- if measured results do not justify a larger move, “do nothing major
  yet” remains the correct outcome

## Constraints

### Environment constraints

- Linux is the primary target.
- Work Mac portability matters, but it is not the current roadmap
  driver.
- Python must remain practical to use and deploy.
- Rust is out of scope for this initiative.

### Functional constraints

- Tools still need to call real APIs such as Jira, n8n, Sonarr,
  Tautulli, and similar systems.
- Safety work is only useful if legitimate tool behavior still works.
- Restricted mode must preserve intended tool access through the host.

### Product constraints

- Keep the effort focused on the runtime itself.
- Do not expand the current phase into a UI, cloud platform, or
  multi-tenant product.

## Explicit Non-goals For The Current Phase

The current phase does **not** include:

- a web UI,
- cloud or multi-tenant product work,
- shared GKE or network-stream deployment,
- a Rust direction,
- a TypeScript or Go rewrite by default,
- dynamic tool creation as a first-phase commitment,
- broad shell/CLI execution as a first-phase commitment,
- broad plugin or platform ecosystem expansion.

Dynamic tool creation, broader CLI execution, richer extensibility, or
alternate deployment models can be revisited later **only after** the
core runtime boundary and restricted-runtime story are proven.

## Review Summary: What Stays, Tightens, Or Moves Later

### Keep

- the brownfield framing around `server.py`, `runner.py`,
  `execution_worker.py`, and `tool_policy.py`
- the decision rule to keep Python by default
- external references as inspiration, not mandates
- “minimal change needed” as a valid outcome

### Tighten

- the first phase so it centers only on benchmark/eval baselining,
  host/runner boundary clarification, and restricted-runtime validation
- the decision gates so alternate runtimes/supervisors require explicit
  proof instead of vague upside
- the handoff so future execution can see which code areas matter most

### Defer

- persistent runners,
- Go supervisor / sidecar exploration,
- alternate runtimes,
- dynamic tool creation,
- broad shell / CLI execution,
- broader platform expansion.

### Remove From First-Phase Assumptions

Do not treat generic optimization backlog work—cold-start tuning,
catalog refresh tweaks, telemetry expansion, or similar cleanup—as the
first milestone unless the benchmark/eval phase proves those items are
the real bottleneck.

## Recommended Direction

### 1. Benchmark first

Before changing architecture, create a baseline that can prove whether
any new design is actually better.

Focus on:

- `search_tools` cold and warm latency,
- `get_tool` latency,
- `run_code` cold and warm latency,
- single-tool orchestration,
- multi-tool orchestration,
- memory behavior,
- timeout behavior,
- failure classification,
- agent accuracy / wrong-tool rate / policy-violation attempts.

This should include both:

- microbenchmarks for runtime overhead,
- functional/safety evals that reflect real agent behavior.

### 2. Tighten the host/runner boundary

This is the most important architectural move.

Target model:

1. Nexus host owns tool discovery, policy, authorization, config,
   logging, and tool execution.
2. Runner executes model-authored orchestration logic.
3. Runner calls tools back through a host boundary instead of importing
   tool-pack modules directly.
4. Policy enforcement remains at the host boundary.

This is the change most likely to improve safety **without** breaking
API-based tools.

### 3. Prove a restricted runtime that still works

The first safety goal is not “maximum sandboxing.” The first safety goal
is:

- block the runner from arbitrary local damage,
- while still allowing approved tool calls to succeed through the host.

Practical first target:

- no direct shell from the runner,
- no arbitrary direct network from the runner,
- no arbitrary local filesystem reach from the runner,
- approved tool access still works through the host.

### 4. Keep alternate backends as evidence-gated follow-ons

Only after the above is proven should Nexus spend serious effort on:

- a persistent Python runner,
- a more restricted Python runner,
- a Go supervisor/sidecar,
- an alternate sandboxed runtime.

These are not rejected permanently. They are **demoted from default
roadmap to gated follow-on options**.

## Phased Plan

## Phase 1 — Prove the current path before optimizing it

Phase 1 is the entire near-term priority. It has three linked
workstreams, and later-phase work must **not** be treated as a
prerequisite for finishing this phase.

### Workstream A — Baseline and evaluation harness

Deliverables:

- benchmark harness,
- repeatable fixture-backed functional checks,
- safety cases,
- agent eval set,
- stored machine-readable baseline results.

### Workstream B — Host/runner boundary clarification

Deliverables:

- an explicit host/runner boundary sketch tied to `server.py`,
  `runner.py`, `execution_worker.py`, and `tool_policy.py`,
- a clear statement that the host owns tool discovery, policy,
  authorization, configuration, logging, and tool execution,
- a narrower runner contract focused on model-authored orchestration
  logic.

### Workstream C — Validate restricted-runtime behavior

Deliverables:

- restricted-runtime validation cases showing what is blocked vs what
  still works,
- proof that allowed tool usage still succeeds through the host
  boundary,
- safety/performance tradeoff data that can be compared against the
  baseline.

### Phase 1 success criteria

- current Nexus behavior is measured rather than guessed,
- there is a clear control baseline for later comparisons,
- the host/runner boundary is concrete enough to prototype without
  reopening requirements,
- restricted-runtime claims are validated against allowed tool
  behavior,
- later architectural claims can be falsified.

Not part of Phase 1 unless the evidence demands it:

- broad performance tuning,
- large telemetry expansion,
- dynamic tool creation,
- broad shell / CLI execution,
- alternate runtime or supervisor implementation work.

### Phase 1 exit rule

Do not advance because a later option sounds attractive. Advance only
when Nexus has:

- a measured benchmark/eval baseline,
- an explicit host/runner boundary,
- a restricted-runtime proof that still preserves approved tool
  workflows,
- enough evidence to decide whether incremental Python work is
  sufficient or a follow-on is justified.

## Phase 2 — Incremental Python improvements only where justified

If Phase 1 shows no material gap, this phase can be skipped.

Focus:

- reduce avoidable cold-start cost if Phase 1 shows it is a meaningful
  bottleneck,
- improve catalog refresh behavior where it affects measured tool-use
  reliability,
- improve structured telemetry and errors where they help explain eval
  failures,
- tighten existing policy enforcement where restricted-runtime
  validation exposed gaps.

Success criteria:

- improvements are tied to measured Phase 1 findings rather than broad
  cleanup,
- no regressions appear in intended tool behavior,
- the remaining gaps are explicit enough to justify either staying on
  Python or testing a follow-on.

## Phase 3 — Explore conditional follow-ons only if justified

Possible follow-ons:

- persistent Python runner,
- Go supervisor/sidecar,
- alternate sandboxed runtime,
- broader extensibility work,
- richer local/CLI workflows.

These happen only if Phase 1 and Phase 2 evidence show a real gap worth
closing.

## What “Evidence” Must Mean

A follow-on or rewrite path should only advance if it shows a clear gain
that matters in practice, such as:

- meaningfully better warm/cold latency,
- materially better failure isolation,
- stronger sandboxing without breaking approved tool workflows,
- cleaner deployment or supervision advantages,
- measurably better agent outcomes.

Vague upside is not enough.

## Decision Gates

### Stay on the current Python-centered path if

- Phase 1 shows acceptable or incrementally improvable latency/accuracy,
- the host/runner boundary can be made explicit without losing tool
  compatibility,
- restricted-runtime safety improves without breaking approved tool
  workflows,
- the deployment story stays simple enough that a bigger runtime shift
  adds more risk than value.

### Explore a follow-on runtime or supervisor only if evidence shows a real gap

A deeper runtime change is justified only if it delivers a **material,
practical** gain in one or more of the following:

- warm or cold latency,
- failure isolation and supervision,
- sandbox strength,
- deployment or operational simplicity,
- agent accuracy and reliability,
- extensibility that the current Python-centered path cannot reasonably
  achieve incrementally.

Reference systems such as `executor`, Cloudflare Code Mode, or related
code-execution products can inform architecture, but their language
choices are **not** evidence by themselves.

### Do nothing major yet if

- the benchmark/eval baseline shows current behavior is already good
  enough,
- the host/runner boundary can be tightened incrementally,
- alternate approaches do not outperform the current path enough to
  justify disruption.

“Do nothing major yet” is a valid conclusion.

## Worktree Strategy

Use separate worktrees for experiments that may diverge significantly:

- baseline / planning,
- benchmark harness,
- runner-boundary prototype,
- supervisor prototype if later justified.

The goal is to keep experiments isolated and comparable without
destabilizing the main branch.

## Final Recommendation

Treat the existing codebase as a starting advantage, not a mistake.

For the next stage of Nexus:

- measure before rewriting,
- prioritize the benchmark/eval baseline,
- make the host/runner boundary explicit,
- prove restricted-runtime behavior without breaking legitimate tool
  access,
- keep Python as the default path unless evidence proves otherwise,
- defer speculative platform expansion,
- preserve minimal change as a valid outcome.


## References
https://www.anthropic.com/engineering/code-execution-with-mcp
https://blog.cloudflare.com/code-mode/
https://x.com/RhysSullivan/status/2030903539871154193
https://github.com/RhysSullivan/executor

- the above git can be cloned locally if required for any reason