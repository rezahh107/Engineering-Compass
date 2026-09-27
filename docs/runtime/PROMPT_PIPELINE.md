# Prompt-Pipeline Integration

## Boundary

Prompt-Pipeline remains an **external source of truth** for prompt-generation routing, intake semantics, templates, validation, and artifact authority.

Engineering Compass does not vendor its rules and does not reuse the retired historical PR-Inspector renderer path.

The inspected integration lock is stored in `integrations/prompt-pipeline.lock.json`. It binds the external repository/commit and governing prompt-generation surfaces. Drift fails closed until the integration is deliberately re-inspected and the lock is updated.

## Current inspected compatibility

- repository: `rezahh107/Prompt-Pipeline`
- inspected commit: `488499d9008b325264159f6c7fc5dbffe4a9e7b2`
- domain: `prompt_generation`
- domain version: `2026.3`
- contract version: `1.1`
- canonical generation path: `pnpm peac:generate -- --request <intake> --mode batch`

The `--request` path is used because Prompt-Pipeline documents it as canonical intake. `--case` is fixture validation and is not the production integration boundary.

## Executable checkout integrity

`LOCK_MATCH` means more than HEAD identity. Immediately before external execution, Engineering Compass requires:

- exact HEAD equals the pinned commit;
- tracked working tree and index equal that HEAD;
- untracked non-ignored files are absent;
- ignored files are rejected unless they are on the explicit generated/install-output allowlist (`node_modules/`, `.pnpm-store/`, `outputs/`, `dist/`, `coverage/`, TypeScript build info, and OS metadata);
- ignored runtime-affecting files such as `.env` are therefore not silently accepted;
- each locked governing file still resolves to its pinned commit blob and its working-file hash matches that blob.

This preserves the external Prompt-Pipeline SSOT while proving the executable source/config checkout, not merely its commit label.

## Handoff

Engineering Compass builds a Prompt-Pipeline intake only after canonical action projection says a prompt is required.

For `IMPLEMENT_REPAIR`, projection supplies the sole canonical `authorized_repair_group_ids`. The handoff serializes exactly those groups and does not reinterpret every `SELECTED` group as authorized. The request also carries exact evidence snapshot identity, confirmed root cause, correct enforcement boundary, selected method, Conformance Lock, falsification obligations, preservation constraints, stop behavior on selected-method infeasibility, and success/failure criteria.

The requested implementation prompt must contain exactly three top-level contracts after a short identity header:

```text
[IMPLEMENTATION CONTRACT]
[VALIDATION CONTRACT]
[POST-IMPLEMENTATION REPORT]
```

## Authority state

Successful generation does not imply downstream authorization. Engineering Compass records Prompt-Pipeline's `authority_state` and `downstream_use_allowed` exactly as returned.

The adapter never auto-approves `review_pending` output and never converts a generated artifact into proof of implementation, test success, CI success, or review completion.

## Commands

```bash
python3 -m engineering_compass prompt-check --prompt-pipeline-root ../Prompt-Pipeline --out /tmp/prompt-pipeline-check.json
python3 -m engineering_compass prompt-handoff --evidence evidence.json --assessment assessment.json --out /tmp/prompt-intake.json
python3 -m engineering_compass compile-prompt --intake /tmp/prompt-intake.json --prompt-pipeline-root ../Prompt-Pipeline --out /tmp/prompt-generation-result.json
```
