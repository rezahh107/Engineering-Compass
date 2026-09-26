# Research Basis

This document records research concepts that inform Engineering Compass. Research supports the reasoning design; it does not create project requirements by itself.

## Architecture quality scenarios

SEI architecture evaluation work uses quality-attribute scenarios to make concerns concrete rather than leaving them as adjectives such as “maintainable” or “robust.”

Engineering Compass adopts the pattern:

`entity property → change/failure stimulus → expected response → architectural obligation`

References:

- SEI / Carnegie Mellon — Architecture Tradeoff Analysis Method (ATAM): https://www.sei.cmu.edu/library/the-architecture-tradeoff-analysis-method/
- SEI ATAM collection: https://insights.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/

## Sensitivity and tradeoff points

ATAM explicitly looks for sensitivity points, tradeoff points, risks, and risk themes.

Engineering Compass uses these ideas to detect cases where small upstream/environment changes create disproportionate downstream effects, and where improving one quality degrades another.

## Architectural decisions and rationale

Architecture research treats important architecture as a set of design decisions and associated rationale, not merely a directory/module diagram.

This supports the decision-centric review unit used here.

Reference:

- Jansen & Bosch, “Software Architecture as a Set of Architectural Design Decisions,” WICSA 2005 / IEEE: https://ieeexplore.ieee.org/document/1620096

## Architecture consistency and erosion

Implementation can drift from intended architecture. Recovering “architecture” only from current code risks treating drift as intent.

Engineering Compass therefore separates:

`Intent ≠ Observed Reality ≠ Engineering Judgment`

Reference:

- Empirical Software Engineering research on architecture consistency/erosion: https://link.springer.com/article/10.1007/s10664-017-9515-3

## Change propagation and temporal evidence

Co-change and architecture-smell research indicates that history can reveal structural hotspots and recurring coupling before or alongside explicit architecture smells.

Engineering Compass treats history as optional discriminating evidence, not mandatory ceremony.

Example reference:

- change coupling / architectural smells study: https://link.springer.com/article/10.1007/s42979-020-00407-5

## Quality-model coverage

ISO/IEC 25010 can serve as a broad coverage ontology for product quality characteristics.

Engineering Compass does **not** run the full standard as a checklist. Quality categories are activated only when material to the target scenario.

Reference:

- ISO/IEC 25010 product quality model: https://committee.iso.org/standard/78176.html

## Strategy selection and adaptive expertise

The repository's core role is closer to strategy selection/metacognitive regulation than knowledge storage: characterize the problem, choose methods, monitor results, adapt, and stop.

Relevant conceptual lines include:

- Rice's Algorithm Selection Problem: choose a method based on problem-instance characteristics.
- metacognitive regulation: planning, monitoring, and evaluation of strategy use.
- adaptive expertise: knowing when efficient routine expertise is insufficient and a different framing/method is required.

Reference:

- Rice, “The Algorithm Selection Problem”: https://www.sciencedirect.com/science/article/abs/pii/S0065245808605203

## Practical repository/agent foundation

The repository foundation follows a self-explaining + self-validating posture, with concise agent instructions pointing to deeper canonical docs and a real verification path.

Current platform references:

- GitHub repository best practices: https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories
- OpenAI Codex / AGENTS.md usage: https://openai.com/index/unrolling-the-codex-agent-loop/
- OpenAI harness engineering pattern — concise `AGENTS.md` as table of contents, deeper docs as system of record: https://openai.com/index/harness-engineering/

## Research guard

Research findings are inputs to review design. They do not override:

- current owner/project authority;
- directly inspected target reality;
- a stronger current official contract;
- evidence that a concept does not fit the target system.
