# Authority, Evidence, and Derivation

## Purpose

Deep engineering review becomes unreliable when project requirements, observed implementation, general best practice, and model preference are mixed into one authority bucket.

Keep them separate.

## Normative authority

Highest first:

1. current explicit owner/project requirements;
2. mandatory product/platform/legal/safety constraints;
3. accepted target-repository product/architecture contracts and valid locks;
4. accepted Engineering Compass canonical review rules within their scope.

Implementation details, prior recommendations, examples, and model confidence do not create owner requirements.

## Epistemic support

Strongest first:

1. current directly inspected target evidence;
2. authoritative external contract/source for the claimed fact;
3. evidence-backed derivation;
4. rebuttable engineering presumption;
5. explicit assumption/hypothesis;
6. unsupported speculation.

Normative authority cannot manufacture facts. Evidence cannot invent permission.

## Intent versus reality versus judgment

Keep three surfaces distinct:

- **Intent:** what the system is supposed to achieve or preserve.
- **Reality:** what the current system, dependencies, environment, and implementation actually do.
- **Judgment:** whether current decisions fit Intent + Reality and whether a better method exists.

Observed implementation is not proof of intended architecture.

## Silence in requirements

Silence does not mean “ignore established engineering concerns.”

When a concern is not explicitly required:

- do not invent a requirement;
- determine whether a structural obligation can be derived from system reality;
- otherwise treat general engineering knowledge as a rebuttable presumption;
- search for a project/technical defeater before issuing a finding.

Example:

A maintained integration on an independently versioned host does not automatically inherit a requirement to support every future version. It does inherit a need for a defined upstream-evolution strategy unless the dependency is intentionally frozen.

## Derivation states

Use visible distinctions such as:

- `EXPLICIT_REQUIREMENT`
- `DERIVED_STRUCTURAL_OBLIGATION`
- `ENGINEERING_PRESUMPTION`
- `ASSUMED`
- `NOT_PROVEN`
- `CONTRADICTED`

A stronger label requires stronger support.

## Lower-level rationalization guard

Do not accept a lower-level implementation document as sufficient justification when the questioned decision is itself defined by that document.

Ask what higher-level purpose, system property, or external constraint required the decision.

## Evidence value test

Before requesting more evidence, ask:

> If this evidence resolves differently, can it change the finding, repair family, risk classification, or next action?

If not, the evidence request is probably unnecessary.

## Claim ceiling

A review claim must not exceed the strongest evidence actually inspected.

Static/source evidence can support source claims. It does not automatically prove production reachability, runtime behavior, operational enforcement, or future compatibility.

`NOT_PROVEN` is a valid result.
