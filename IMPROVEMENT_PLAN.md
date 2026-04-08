# Improvement Plan

## Goal

Improve Nexus into a faster, safer, more reliable agent tooling runtime **for the codebase that already exists**, without turning the effort into a speculative rewrite or a broader product/platform project.

This plan is Linux-first, keeps later Mac portability in view, and treats language/runtime changes as **evidence-gated decisions** rather than assumed upgrades.

## What This Plan Is Optimizing For

Prioritize changes only when they produce meaningful gains in one or more of these areas:

- runtime speed and latency,
- agent accuracy and tool-use reliability,
- practical sandboxing and safety,
- extensibility that improves the runtime itself,
- deployment simplicity for real use.

If the evidence shows the current architecture is already good enough, **minimal change or no change is an acceptable result**.

## Brownfield Facts That Matter

Nexus is not starting from zero. The repository already contains the main primitives this effort is about:

- `nexus/server.py` exposes the narrow MCP surface: `run_code`, `search_tools`, `get_tool`
- `nexus/runner.py` already executes model-authored Python and exposes `TOOLS` / `load_tool(...)`
- `nexus/execution_worker.py` already provides subprocess execution scaffolding
- `nexus/tool_policy.py` already implements unrestricted/restricted policy concepts and named presets

That means the strongest near-term opportunity is not “pick a better language”.
The strongest near-term opportunity is to:

1. measure the current system properly,
2. tighten the host/runner boundary,
3. validate safer restricted-runtime behavior,
4. only then decide whether alternate runtimes or supervisors are justified.

## Decision Rule

Default stance:

- **keep Python unless evidence proves a materially better path**.

Do **not** pursue TypeScript, Go, or another runtime just because reference systems such as `executor`, Code Mode, or related tooling are built that way.

A larger rewrite or different runtime is justified only if it demonstrates a **substantial, practical** gain in:

- performance,
- agent accuracy,
- sandboxing/safety,
- or extensibility

that the current Python-centered architecture cannot reasonably achieve incrementally.

Rust is out of scope for this initiative.

## External Reference Points

This plan is informed by:

- Rhys Sullivan’s `executor`
- Cloudflare Code Mode
- Anthropic’s MCP code-execution guidance

These references are useful for architectural ideas, especially:

- host/runner separation,
- controlled execution environments,
- tool invocation through a narrow boundary,
- approval/gating patterns when useful.

They are **not** taken as proof that Nexus should be rewritten around their language or product choices.

## Constraints

### Environment

- Linux is the primary target.
- Work Mac portability matters, but it is a guardrail, not today’s main driver.
- Python must remain easy to use and deploy.
- Rust must not become a requirement.

### Functional constraints

- Tools still need to call real APIs such as Jira, n8n, Sonarr, Tautulli, and similar systems.
- Safety work is only useful if legitimate tool behavior still works.
- Restricted mode must preserve intended tool access through the host.

### Product constraints

- No web UI.
- No cloud or multi-tenant product surface.
- No shared GKE/network-stream deployment in this phase.
- Do not expand this into a general runtime platform project.

## Explicit Non-goals For The Current Phase

The current phase does **not** include:

- a web UI,
- cloud or multi-tenant architecture,
- running Nexus as a shared GKE service,
- a Rust direction,
- a TypeScript or Go rewrite by default,
- dynamic tool creation by agents as a first-phase commitment,
- broad shell/CLI execution as a first-phase commitment,
- broad plugin/platform ecosystem expansion.

Dynamic tool creation and broader CLI execution can be revisited later **only after** the core runtime boundary and restricted-runtime story are proven.

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

## Phase 0 — Baseline and evaluation harness

Deliverables:

- benchmark harness,
- repeatable fixture-backed functional checks,
- safety cases,
- agent eval set,
- stored machine-readable results.

Success criteria:

- current Nexus behavior is measured rather than guessed,
- there is a clear control baseline for later comparisons,
- later architectural claims can be falsified.

## Phase 1 — Improve the current Python path

Focus:

- reduce avoidable cold-start cost,
- improve catalog refresh behavior,
- improve structured telemetry and errors,
- tighten existing policy enforcement,
- identify the real baseline to beat.

Success criteria:

- measurable improvement or at least trustworthy baseline visibility,
- no regressions in intended tool behavior,
- clearer operational understanding of where current costs really are.

## Phase 2 — Establish a strict host/runner boundary

Focus:

- define the runner protocol,
- move tool execution responsibility fully to the host,
- make runner behavior narrower and easier to restrict,
- preserve existing tool-pack functionality.

Success criteria:

- tools still work through the host,
- runner no longer needs direct tool-pack imports,
- policy semantics remain consistent,
- the boundary is explicit enough to support later restriction or backend swaps.

## Phase 3 — Validate restricted runtime behavior

Focus:

- restrict direct runner capabilities,
- test blocked behaviors explicitly,
- confirm allowed tool calls still function,
- gather safety/performance tradeoff data.

Success criteria:

- bad runner behaviors are blocked or terminated,
- legitimate tool usage still works,
- logs and error reporting make failures understandable.

## Phase 4 — Explore conditional follow-ons only if justified

Possible follow-ons:

- persistent Python runner,
- Go supervisor/sidecar,
- alternate sandboxed runtime,
- broader extensibility work.

These happen only if earlier evidence shows a real gap worth closing.

## What “Evidence” Must Mean

A follow-on or rewrite path should only advance if it shows a clear gain that matters in practice, such as:

- meaningfully better warm/cold latency,
- materially better failure isolation,
- stronger sandboxing without breaking approved tool workflows,
- cleaner deployment or supervision advantages,
- measurably better agent outcomes.

Vague upside is not enough.

## Valid Future Branches

These are valid later branches, not current commitments:

- Go as a supervisor or deployment helper,
- alternate sandbox runtimes,
- broader tool/runtime extensibility,
- richer local/CLI workflows.

The plan should pivot toward them **only** when benchmark and restricted-runtime evidence justify it.

## Worktree Strategy

Use separate worktrees for experiments that may diverge significantly:

- baseline / planning,
- benchmark harness,
- runner-boundary prototype,
- supervisor prototype if later justified.

The goal is to keep experiments isolated and comparable without destabilizing the main branch.

## Suggested Repository Additions

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

These additions should only appear when they support the active phase.

## Decision Gates

### Keep the current Python-centered direction if

- performance is acceptable or incrementally improvable,
- the host/runner boundary can be made explicit,
- restricted-runtime safety can be improved without breaking tools,
- the deployment story stays simple.

### Explore a Go supervisor if

- supervision/lifecycle/resource management becomes a real pain point,
- deployment/distribution clearly improves,
- the benefit is operationally meaningful rather than theoretical.

### Explore an alternate runtime if

- Python remains too weak after the host/runner boundary is tightened,
- the safety gap is still unacceptable,
- or extensibility/agent behavior clearly demands a different execution model.

### Do nothing major yet if

- the benchmark/eval harness shows current behavior is already acceptable,
- or the proposed alternatives do not produce enough benefit to justify disruption.

## Success Criteria

This effort is successful when Nexus has:

- an evidence-backed runtime roadmap,
- a measured baseline instead of assumptions,
- a clearer host/runner split,
- a safer restricted-runtime direction that still preserves legitimate tool behavior,
- a narrowed first phase with explicit non-goals,
- a roadmap that can justify either incremental progress or minimal change.

## Near-Term Execution Order

1. Build the benchmark and evaluation harness.
2. Measure the current Python path.
3. Tighten the host/runner boundary.
4. Validate restricted-runtime behavior.
5. Reassess whether persistent runners, supervisors, or alternate runtimes are still justified.
6. Only then expand into follow-on capabilities if the evidence supports it.

## Final Recommendation

For the next stage of Nexus:

- treat the current codebase as the starting advantage, not a mistake,
- keep Python by default,
- measure before rewriting,
- prioritize host/runner separation and restricted-runtime proof,
- defer speculative platform expansion,
- and allow “minimal change needed” to remain a valid outcome.
