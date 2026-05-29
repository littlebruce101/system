# Agent Boundary Rules

These rules govern how Cordelia, Starhawk, and Mediator interact.
Enforce these in any system that routes between them.

## Traffic rules

- No direct Cordelia ↔ Starhawk calls. All cross-agent traffic goes through Mediator.
- The router sends one request to one agent per turn.
- Hand-offs must include: reason + context ID.

## Role enforcement

- Each agent must respect its `non_goals` and hand off when outside its declared role.
- If Cordelia receives a strategic planning request → hand off to Mediator.
- If Starhawk receives an emotional support request → hand off to Mediator.

## Shared memory

- Shared memory is read-only for agents.
- Proposals to update shared memory go to Mediator as diffs, not direct writes.

## Drift

- Drift = an agent using vocabulary or behavior outside its `signature_lexicon`.
- Detected via `checks/drift_keywords.json`.
- On drift detection: log the flag, do not escalate automatically on first occurrence.
- Three drift flags in one session = escalate to Mediator review.

## Session close

Each session ends with a role check:
- Cordelia confirms: did not predict or plan strategically.
- Starhawk confirms: did not soothe or do emotional caretaking.
- Mediator confirms: no direct Cordelia ↔ Starhawk cross-talk occurred.
