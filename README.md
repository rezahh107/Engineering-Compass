# Engineering Compass

Guides LLMs to choose, sequence, and adapt the right engineering reasoning methods for each code and architecture review.

> **Start here:** read [`AGENT_ENTRYPOINT.md`](AGENT_ENTRYPOINT.md) before using this repository as review guidance.

## Mission

Engineering Compass does **not** teach an LLM software engineering from scratch and it is not a giant code-quality checklist. The model already knows many engineering methods. This repository governs **when and how to apply that expertise**:

`characterize the situation → select reasoning methods → sequence them → monitor evidence → adapt → stop at sufficiency`

The target is deeper engineering judgment: identify material system obligations, challenge architecture and implementation decisions at the right abstraction level, and prefer the smallest root-correct improvement.

## What this repository is

A version-controlled reasoning-governance repository for deep engineering review of:

- pull-request changes;
- repository-wide architecture;
- dependency and lifecycle decisions;
- capability and structural-obligation gaps;
- sensitivity and tradeoff points;
- root-cause and risk-theme analysis;
- materially better implementation or architecture alternatives.

## What this repository is not

- a linter or static-analysis replacement;
- a language/framework tutorial;
- an encyclopedic catalog of anti-patterns;
- a generic security/compliance checklist;
- proof that a review is correct merely because these Markdown files exist;
- a multi-agent execution orchestrator.

## Canonical reasoning path

The core reasoning model is documented in [`docs/core/REASONING_MODEL.md`](docs/core/REASONING_MODEL.md).

At a high level:

`Intent → System Inventory → Material Properties → Scenarios → Structural Obligations → Required Capabilities → Engineering Decisions → Strategy Selection → Sensitivity/Tradeoffs → Root Cause/Risk Themes → Same-Level Alternatives → Depth/Blast Radius → Smallest Root-Correct Improvement`

## Repository map

- [`AGENT_ENTRYPOINT.md`](AGENT_ENTRYPOINT.md) — selective read order and operating boundary.
- [`AGENTS.md`](AGENTS.md) — concise agent-facing operational entrypoint.
- [`repository.manifest.json`](repository.manifest.json) — phase, canonical surfaces, and verification contract.
- [`docs/core/MISSION.md`](docs/core/MISSION.md) — purpose, scope, and non-goals.
- [`docs/core/REASONING_MODEL.md`](docs/core/REASONING_MODEL.md) — canonical reasoning architecture.
- [`docs/governance/AUTHORITY.md`](docs/governance/AUTHORITY.md) — authority, evidence, and derivation rules.
- [`docs/governance/REVIEW_PROTOCOL.md`](docs/governance/REVIEW_PROTOCOL.md) — PR/repository review procedure.
- [`docs/governance/VERIFICATION.md`](docs/governance/VERIFICATION.md) — what repository verification does and does not prove.
- [`docs/research/RESEARCH_BASIS.md`](docs/research/RESEARCH_BASIS.md) — research concepts that inform the design.
- [`fixtures/gravity-flow-version-coupling.json`](fixtures/gravity-flow-version-coupling.json) — first semantic regression fixture.
- [`scripts/verify_repo.py`](scripts/verify_repo.py) — canonical repository verification command.

## Verification

Run:

```bash
python3 scripts/verify_repo.py
```

CI executes the same underlying verification contract.

This verifies repository structure, machine-readable artifacts, and local documentation links. It does **not** prove that an LLM will make correct engineering judgments. Semantic review quality remains a separate evaluation boundary described in the verification document.

## Change model

Material reasoning/governance changes should be proposed on a branch, reviewed as a pull request, verified on the exact resulting Head, and accepted only when merged to `main`.

The initial Foundation baseline has already been accepted by the human-approved merge of PR #1 to `main`. Its historical commit/tree identity is recorded in `repository.manifest.json`; later repository changes do not rewrite that baseline identity.
