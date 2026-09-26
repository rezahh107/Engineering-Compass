# Engineering Compass

Guides LLMs to choose, sequence, adapt, and **operationalize** the right engineering reasoning methods for code and architecture review.

> **Start here:** read [`AGENT_ENTRYPOINT.md`](AGENT_ENTRYPOINT.md).

## Mission

Engineering Compass does **not** teach an LLM software engineering from scratch and it is not a giant code-quality checklist. The model already knows many engineering methods. This repository governs **when and how to apply that expertise**:

`characterize → select methods → sequence → observe evidence → adapt → evaluate → stop`

It now also provides an executable control plane around that judgment:

`verified target → evidence bundle → LLM assessment → root-cause repair validation → canonical action → Prompt-Pipeline handoff`

The target is deeper engineering judgment with controlled execution: identify material system obligations, challenge architecture and implementation decisions at the right abstraction level, find the causal mechanism, compare materially distinct repair families, lock the selected method, require falsification, and emit a bounded next action without collapsing review into implementation.

## What this repository is

A version-controlled reasoning and review-control system for:

- pull-request review (`PR_SCOPE`);
- branch/ref delta review (`REF_DELTA_SCOPE`);
- repository-wide review (`REPOSITORY_SCOPE`);
- dependency and lifecycle decisions;
- capability and structural-obligation gaps;
- sensitivity and tradeoff points;
- root-cause and risk-theme synthesis;
- root-complete comparative repair selection;
- deterministic action routing;
- Prompt-Pipeline-backed implementation/verification handoff.

## What this repository is not

- a linter or static-analysis replacement;
- a language/framework tutorial;
- an encyclopedic catalog of anti-patterns;
- proof that an LLM judgment is correct merely because its JSON is schema-valid;
- a replacement for Prompt-Pipeline;
- a PR-Inspector dependency;
- an automatic merger/deployer or remote-write orchestrator.

## Canonical reasoning path

[`docs/core/REASONING_MODEL.md`](docs/core/REASONING_MODEL.md) defines the reasoning model:

`Intent → System Inventory → Material Properties → Scenarios → Structural Obligations → Required Capabilities → Engineering Decisions → Strategy Selection → Sensitivity/Tradeoffs → Root Cause/Risk Themes → Same-Level Alternatives → Depth/Blast Radius → Smallest Root-Correct Improvement`

The executable runtime is documented in [`docs/runtime/ARCHITECTURE.md`](docs/runtime/ARCHITECTURE.md).

## Executable runtime

The Python package uses only the standard library.

### 1. Collect target evidence

```json
{
  "target": {"kind": "PR_SCOPE", "repository": "owner/repository", "pr_number": 42},
  "review_intent": "Deep engineering review of the changed decisions.",
  "inspection_profile": "deep"
}
```

```bash
python3 -m engineering_compass collect --request request.json --out evidence.json
```

`GITHUB_TOKEN` is optional for public repositories and recommended when authenticated/rate-limited evidence access is required. The collector is read-only.

### 2. Have the LLM produce the bounded assessment

Use the evidence bundle plus the canonical reasoning docs. See [`docs/runtime/LLM_ASSESSMENT_CONTRACT.md`](docs/runtime/LLM_ASSESSMENT_CONTRACT.md).

### 3. Project the next action

```bash
python3 -m engineering_compass project --evidence evidence.json --assessment assessment.json --out action.json
```

The runtime will not permit a code-modifying action merely because a Finding exists.

### 4. Build Prompt-Pipeline handoff when required

```bash
python3 -m engineering_compass prompt-handoff --evidence evidence.json --assessment assessment.json --out prompt-intake.json
```

### 5. Compile through the locked external Prompt-Pipeline checkout

```bash
python3 -m engineering_compass compile-prompt --intake prompt-intake.json --prompt-pipeline-root ../Prompt-Pipeline --out prompt-generation-result.json
```

Engineering Compass preserves Prompt-Pipeline's returned authority state. Generation is not auto-approval.

## Root-complete repair invariant

No direct `Finding → Implementation Prompt` path exists.

`Finding(s) → Root-Cause Anchor → BOUNDED/FULL route → candidate methods → selected method → defect-class closure → Conformance Lock → falsification obligations → action projection → Prompt-Pipeline`

See [`docs/runtime/ROOT_CAUSE_REPAIR.md`](docs/runtime/ROOT_CAUSE_REPAIR.md).

## Repository map

- [`AGENT_ENTRYPOINT.md`](AGENT_ENTRYPOINT.md) — selective runtime read order.
- [`AGENTS.md`](AGENTS.md) — concise contributor/agent instructions.
- [`repository.manifest.json`](repository.manifest.json) — canonical surfaces, phase, runtime and verification status.
- [`docs/core/`](docs/core/) — mission and reasoning semantics.
- [`docs/governance/`](docs/governance/) — authority, review and verification contracts.
- [`docs/runtime/`](docs/runtime/) — executable runtime, root-cause, action and Prompt-Pipeline contracts.
- [`engineering_compass/`](engineering_compass/) — executable control-plane package.
- [`schemas/`](schemas/) — machine-readable contract views.
- [`fixtures/runtime/`](fixtures/runtime/) — executable runtime regression fixtures.
- [`integrations/prompt-pipeline.lock.json`](integrations/prompt-pipeline.lock.json) — inspected Prompt-Pipeline compatibility lock.
- [`scripts/verify_repo.py`](scripts/verify_repo.py) — canonical repository verifier.

## Verification

```bash
python3 scripts/verify_repo.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

CI executes repository/runtime verification and separately checks the locked Prompt-Pipeline checkout. Structural/runtime PASS proves only the transitions and invariants actually exercised; it does **not** prove that an LLM discovered the objectively correct root cause or best engineering method.

## Change model

Material reasoning/governance/runtime changes should be proposed on a branch, reviewed as a pull request, verified on the exact resulting Head, and accepted only when merged to `main`.

The initial Foundation baseline remains the human-approved PR #1 merge recorded in `repository.manifest.json`; later runtime additions do not rewrite that historical baseline identity.
