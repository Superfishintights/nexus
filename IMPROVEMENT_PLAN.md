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

## Current-Phase Scope

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

Dynamic tool creation, broader CLI execution, richer extensibility, or alternate deployment models can be revisited later only if the earlier evidence shows a real gap worth solving.

## Decision Gates

### Stay on the current Python-centered path if

- latency is acceptable or incrementally improvable,
- the host/runner boundary can be made explicit,
- restricted-runtime safety improves without breaking tools,
- deployment remains simpler than the alternatives,
- and agent outcomes do not show a meaningful deficit.

### Explore a follow-on runtime or supervisor only if evidence shows a real gap

A deeper runtime change is justified only if it delivers a **material, practical** gain in one or more of the following:

- warm or cold latency,
- failure isolation and supervision,
- sandbox strength,
- deployment or operational simplicity,
- agent accuracy and reliability,
- extensibility that the current Python-centered path cannot reasonably achieve incrementally.

Reference systems such as `executor`, Cloudflare Code Mode, or related code-execution products can inform architecture, but their language choices are **not** evidence by themselves.

### Do nothing major yet if

- the benchmark/eval baseline shows current behavior is already good enough,
- the host/runner boundary can be tightened incrementally,
- and alternate approaches do not outperform the current path enough to justify disruption.

“Do nothing major yet” is a valid conclusion.

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
3. Clarify and tighten the host/runner boundary.
4. Validate restricted-runtime behavior against real tool workflows.
5. Reassess whether persistent runners, supervisors, or alternate runtimes are still justified.
6. Expand scope only if the measured results justify it.

## Final Recommendation

Treat the existing codebase as a starting advantage, not a mistake.

For the next stage of Nexus:

- measure before rewriting,
- prioritize the benchmark/eval baseline,
- make the host/runner boundary explicit,
- prove restricted-runtime behavior without breaking legitimate tool access,
- keep Python as the default path unless evidence proves otherwise,
- defer speculative platform expansion,
- and preserve minimal change as a valid outcome.
