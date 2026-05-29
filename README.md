# agent-router

Keyword-based routing between two AI agent personas with drift detection.

## Agents

| Agent | Role | Non-goals |
|-------|------|-----------|
| Cordelia | Inner guidance, memory tending | Prediction, strategic planning, routing |
| Starhawk | Foresight, navigation, scenario planning | Emotional caretaking, memory stewardship |
| Mediator | Cross-agent traffic, hand-offs | — |

Full identity specs: `cordelia.identity.yaml`, `starhawk.identity.yaml`

## How it works

```
prompt
↓
router_rules.py — keyword scoring
↓
cordelia | starhawk | mediator
↓
response checked against drift_keywords.json
↓
drift flags logged if agent vocabulary is out of role
```

## Files

| File | Purpose |
|------|---------|
| `router_rules.py` | Route a prompt + check response for drift |
| `cordelia.identity.yaml` | Cordelia identity constraints |
| `starhawk.identity.yaml` | Starhawk identity constraints |
| `checks/drift_keywords.json` | Words that indicate an agent is out of role |
| `boundaries.md` | Traffic rules — no direct agent cross-talk |
| `.github/pull_request_template.md` | PR owner + cross-talk risk checklist |

## Usage

```bash
python router_rules.py "I feel overwhelmed and don't know what to do"
# Agent: cordelia

python router_rules.py "What are my options before the Friday deadline?"
# Agent: starhawk

python router_rules.py "Help me think through both sides of this"
# Agent: mediator
```

## Boundary rules

All agent cross-traffic goes through Mediator. No direct Cordelia ↔ Starhawk calls.
See `boundaries.md` for full rules.
