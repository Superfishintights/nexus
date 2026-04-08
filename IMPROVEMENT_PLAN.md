# Improvement Plan

## Decision Summary

Nexus should improve as a **brownfield agent runtime** built from the code that already exists, not as a speculative rewrite or a broader platform project.

Default decision rule:

- **Keep Python unless evidence proves a materially better path.**
- Treat alternate runtimes, supervisors, and deeper platform expansion as **follow-on options**, not default roadmap commitments.
- Treat **minimal change or no major rewrite** as a valid outcome if the evidence says the current architecture is already good enough.

## What This Plan Is Optimizing For

Only prioritize changes that produce practical gains in one or more of these areas:

- runtime speed and latency,
- agent accuracy and tool-use reliability,
- sandboxing and safety,
- runtime extensibility that improves Nexus itself,
- deployment and operational simplicity.

This is a Linux-first plan. Mac portability matters, but it is a guardrail rather than the main driver of the current phase.

## Brownfield Grounding

The repository already contains the core primitives this plan is about:

- `nexus/server.py` exposes the narrow MCP surface around `run_code`, `search_tools`, and `get_tool`.
- `nexus/runner.py` already executes model-authored Python and exposes `TOOLS` plus `load_tool(...)`.
- `nexus/execution_worker.py` already provides subprocess execution scaffolding.
- `nexus/tool_policy.py` already contains restricted-policy concepts and presets.

Because these primitives already exist, the strongest near-term opportunity is **not** “pick a new language.”
The strongest near-term opportunity is to:

1. measure the current runtime,
2. tighten the host/runner boundary,
3. validate a restricted runtime that still supports legitimate tool usage,
4. only then decide whether deeper runtime changes are justified.

## Primary Code Touchpoints

Later execution or review work should stay grounded in these files:

- `nexus/server.py` — public MCP boundary and current tool-discovery / tool-metadata surface
- `nexus/runner.py` — execution globals, lazy tool loading, limits, and runner behavior
- `nexus/execution_worker.py` — subprocess execution boundary for bounded runs
- `nexus/tool_policy.py` — policy modes, presets, authorization semantics, and restricted-mode expectations

If a proposed roadmap change does not clearly relate back to one or more of these touchpoints, it is probably too speculative for the current phase.

## Decision Rule

The current phase must stay narrow and evidence-driven.

### Phase 1 — Prove the core runtime boundary

Phase 1 is complete only when Nexus has made concrete progress on all three of these workstreams:

1. **Benchmark and eval baseline**
   - Measure `search_tools`, `get_tool`, and `run_code` in cold and warm cases.
   - Capture single-tool and multi-tool orchestration behavior.
   - Record timeout, memory, failure-mode, and wrong-tool / policy-violation behavior.
   - Store results in a repeatable, machine-readable form.

2. **Host/runner boundary clarification**
   - Make the host responsible for tool discovery, policy, authorization, configuration, logging, and tool execution.
   - Narrow the runner so it focuses on model-authored orchestration logic.
   - Move toward runner-to-host tool calls through an explicit boundary instead of direct tool-pack coupling.

3. **Restricted-runtime validation**
   - Prove that the runner can be meaningfully constrained without breaking intended tool workflows.
   - First target: no arbitrary direct shell/CLI, network, or filesystem access from the runner.
   - Approved tool access must still work through the host boundary.

### Current-phase success criteria

The current phase is successful when:

- Nexus has a trustworthy benchmark/eval baseline instead of assumptions.
- The host/runner split is explicit enough to support later restriction or backend swaps.
- Restricted-runtime tests show bad runner behavior is blocked or terminated.
- Legitimate API-based tool workflows still work.
- The resulting data is strong enough to justify either incremental improvement or no major rewrite.

## Constraints

### Environment constraints

- Linux is the primary target.
- Work Mac portability matters, but it is not the current roadmap driver.
- Python must remain practical to use and deploy.
- Rust is out of scope for this initiative.

### Functional constraints

- Tools still need to call real APIs such as Jira, n8n, Sonarr, Tautulli, and similar systems.
- Safety work is only useful if legitimate tool behavior still works.
- Restricted mode must preserve intended tool access through the host.

### Product constraints

- Keep the effort focused on the runtime itself.
- Do not expand the current phase into a UI, cloud platform, or multi-tenant product.

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

Dynamic tool creation and broader CLI execution can be revisited later **only after** the core runtime boundary and restricted-runtime story are proven.

## Review Summary: What Stays, Tightens, Or Moves Later

### Keep

- the brownfield framing around `server.py`, `runner.py`, `execution_worker.py`, and `tool_policy.py`
- the decision rule to keep Python by default
- external references as inspiration, not mandates
- “minimal change needed” as a valid outcome

### Tighten

- the first phase so it centers only on benchmark/eval baselining, host/runner boundary clarification, and restricted-runtime validation
- the decision gates so alternate runtimes/supervisors require explicit proof instead of vague upside
- the handoff so future execution can see which code areas matter most

### Defer

- persistent runners,
- Go supervisor / sidecar exploration,
- alternate runtimes,
- dynamic tool creation,
- broad shell / CLI execution,
- broader platform expansion.

### Remove From First-Phase Assumptions

Do not treat generic optimization backlog work—cold-start tuning, catalog refresh tweaks, telemetry expansion, or similar cleanup—as the first milestone unless the benchmark/eval phase proves those items are the real bottleneck.

## Recommended Direction

### 1. Benchmark first

Before changing architecture, create a baseline that can prove whether any new design is actually better.

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

1. Nexus host owns tool discovery, policy, authorization, config, logging, and tool execution.
2. Runner executes model-authored orchestration logic.
3. Runner calls tools back through a host boundary instead of importing tool-pack modules directly.
4. Policy enforcement remains at the host boundary.

This is the change most likely to improve safety **without** breaking API-based tools.

### 3. Prove a restricted runtime that still works

The first safety goal is not “maximum sandboxing”.
The first safety goal is:

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

These are not rejected permanently.
They are **demoted from default roadmap to gated follow-on options**.

## Phased Plan

## Phase 1 — Prove the current path before optimizing it

This phase is intentionally narrow. It exists to answer what Nexus should do next, not to pre-commit to a larger rewrite.

Deliverables:

- benchmark harness,
- repeatable fixture-backed functional checks,
- safety cases,
- agent eval set,
- stored machine-readable baseline results,
- an explicit host/runner boundary sketch tied to `server.py`, `runner.py`, `execution_worker.py`, and `tool_policy.py`,
- restricted-runtime validation cases that show what is blocked vs what still works.

Success criteria:

- current Nexus behavior is measured rather than guessed,
- there is a clear control baseline for later comparisons,
- the host/runner boundary is concrete enough to prototype without reopening requirements,
- restricted-runtime claims are validated against allowed tool behavior,
- later architectural claims can be falsified.

Not part of Phase 1 unless the evidence demands it:

- broad performance tuning,
- large telemetry expansion,
- dynamic tool creation,
- broad shell / CLI execution,
- alternate runtime or supervisor implementation work.

## Phase 2 — Improve the current Python path only where Phase 1 proves it matters

Focus:

- reduce avoidable cold-start cost when benchmarks show it matters,
- improve catalog refresh behavior when it is a measured pain point,
- improve structured telemetry and errors where validation gaps were exposed,
- tighten policy enforcement where restricted-runtime tests found real weaknesses.

Success criteria:

- changes are justified by Phase 1 evidence,
- there is measurable improvement in the targeted pain points,
- intended tool behavior does not regress,
- the deployment story remains simple.

## Phase 3 — Explore conditional follow-ons only if justified

Possible follow-ons:

- persistent Python runner,
- Go supervisor/sidecar,
- alternate sandboxed runtime,
- broader extensibility work,
- richer local/CLI workflows.

These happen only if Phase 1 and Phase 2 evidence show a real gap worth closing.

## What “Evidence” Must Mean

A follow-on or rewrite path should only advance if it shows a clear gain that matters in practice, such as:

- meaningfully better warm/cold latency,
- materially better failure isolation,
- stronger sandboxing without breaking approved tool workflows,
- cleaner deployment or supervision advantages,
- measurably better agent outcomes.

Vague upside is not enough.

## Decision Gates

### Stay on the current Python-centered path if

- Phase 1 shows acceptable or incrementally improvable latency/accuracy,
- the host/runner boundary can be made explicit without losing tool compatibility,
- restricted-runtime safety improves without breaking approved tool workflows,
- the deployment story stays simple enough that a bigger runtime shift adds more risk than value.

### Explore a follow-on runtime or supervisor only if evidence shows a real gap

- supervision, lifecycle control, or resource isolation remains a demonstrated pain point after Phase 1/2 work,
- deployment or distribution would become materially simpler,
- the gain is operationally meaningful rather than theoretical.

- warm or cold latency,
- failure isolation and supervision,
- sandbox strength,
- deployment or operational simplicity,
- agent accuracy and reliability,
- extensibility that the current Python-centered path cannot reasonably achieve incrementally.

- Python still misses the benchmark, safety, or extensibility bar after the host/runner boundary is tightened,
- restricted-runtime validation still leaves an unacceptable gap,
- or measured agent behavior clearly demands a different execution model.

### Do nothing major yet if

- the benchmark/eval baseline shows current behavior is already good enough,
- the host/runner boundary can be tightened incrementally,
- and alternate approaches do not outperform the current path enough to justify disruption.

## Worktree Strategy

Use separate worktrees for experiments that may diverge significantly:

- baseline / planning,
- benchmark harness,
- runner-boundary prototype,
- supervisor prototype if later justified.

The goal is to keep experiments isolated and comparable without destabilizing the main branch.

## Possible Repository Additions When A Phase Needs Them

Add incrementally, not all at once:

- `benchmarks/README.md`
- `benchmarks/cases/`
- `benchmarks/results/`
- `benchmarks/fixtures/`
- `scripts/bench.py`
- `scripts/bench_compare.py`
- `scripts/run_eval.py`
- `scripts/fixture_api_server.py`
- `nexus/runner_protocol.py`
- `nexus/runner_backends/`

These additions should only appear when they support the active phase and should not be treated as hidden prerequisites for approving Phase 1.

## Success Criteria

## Later-Only Follow-ons

These are valid later branches, not current commitments:

- a persistent Python runner,
- a more restricted Python execution path,
- a Go supervisor or sidecar,
- an alternate sandboxed runtime,
- dynamic tool creation,
- broader shell/CLI execution,
- broader runtime extensibility work.

Each of these stays deferred until Phase 1 evidence shows why it is needed.

## Codebase Areas That Matter Most

Downstream planning and execution should stay anchored to these files first:

- `nexus/server.py` — MCP surface, request handling, and the host-side API contract.
- `nexus/runner.py` — model-authored code execution behavior and runner-facing capabilities.
- `nexus/execution_worker.py` — subprocess execution path and execution isolation scaffolding.
- `nexus/tool_policy.py` — restricted/unrestricted policy behavior and enforcement assumptions.

If a proposed direction cannot explain how it improves or preserves behavior around those touchpoints, it is not ready to become roadmap priority.

## Execution Order

1. Build the benchmark and eval harness.
2. Measure the current Python path.
3. Define the host/runner boundary from the current codebase touchpoints.
4. Validate restricted-runtime behavior against allowed tool workflows.
5. Decide whether targeted Python improvements are justified.
6. Only then consider persistent runners, supervisors, alternate runtimes, or broader runtime features.

## Final Recommendation

Treat the existing codebase as a starting advantage, not a mistake.

For the next stage of Nexus:

- measure before rewriting,
- narrow the first phase to benchmarks/evals, host/runner clarification, and restricted-runtime proof,
- defer speculative platform expansion,
- and preserve minimal change as a valid outcome.
