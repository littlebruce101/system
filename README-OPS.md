# Operations

## Running the router

```bash
python router_rules.py "<prompt>"
python router_rules.py "<prompt>" --response "<agent response>"
```

Returns: agent name, keyword signals, drift flags (if any).
Pass `--response` to also check an agent's reply for drift vocabulary.

## Updating routing rules

Edit `router_rules.py` → `ROUTING_RULES` dict.
Add keywords to `"cordelia"` or `"starhawk"` lists.

## Updating drift detection

Edit `checks/drift_keywords.json`.
- `cordelia_flags` — words that indicate Cordelia is acting like Starhawk
- `starhawk_flags` — words that indicate Starhawk is acting like Cordelia

## PR workflow

Every PR must:
1. Select one owner in `.github/pull_request_template.md` (Cordelia / Starhawk / Mediator / Shared)
2. Document any cross-talk risks
3. Include a rollback plan

## Adding a new agent

1. Create `<name>.identity.yaml` following the existing format
2. Add routing keywords to `ROUTING_RULES` in `router_rules.py`
3. Add drift flags to `checks/drift_keywords.json`
4. Update `boundaries.md` with any new traffic rules
