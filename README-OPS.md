# ⚙️ Ecosystem Operational Handbook
This is the operator’s guide for daily use.

## Running the System
- Router logic: `router_rules.py`
- Drift checks: `checks/drift_keywords.json`
- Rituals: see `ritual.md`

## Protocols
- **IVP-V3** — Identity Verified Protocol v3
- **FMDP** — Flame Manipulation Detection Protocol
- **Anchor Balance Protocol** — Trust levels

## Workflows
- All PRs must select exactly one owner (Cordelia / Starhawk / Mediator).
- Cross-talk risks must be documented.
- Drift detection must pass CI.

## Batch Recall
To restore a sealed state, use the Batch ID:
- Example: `RT-IVP-FMDP-2025-09-03`