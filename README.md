# agent-router

Routes your question to the right AI persona (Cordelia or Starhawk) and answers it via ChatGPT.

## Agents

| Agent | Role |
|-------|------|
| Cordelia | Inner guidance, clarity, reflection |
| Starhawk | Strategy, options, foresight |
| Mediator | Both — used when the question doesn't clearly fit one |

## Setup

```bash
pip install openai python-dotenv
cp .env.example .env   # add your OpenAI API key
```

`.env` file:
```
OPENAI_API_KEY=your_key_here
```

## Usage

```bash
# Auto-routed (system picks the persona)
python main.py "I don't know how to handle this situation"
python main.py "What are my options before the deadline?"

# Force a persona
python main.py --persona cordelia "Walk me through what I'm feeling"
python main.py --persona starhawk "Map out the risks here"

# Show routing decision
python main.py --show-routing "Should I take this job offer?"
```

## How routing works

```
your question
↓
keyword scoring (router_rules.py)
↓
cordelia | starhawk | mediator
↓
system prompt selected
↓
sent to ChatGPT (gpt-4o-mini)
↓
response checked for drift
```

Drift = when an agent's response contains vocabulary outside its declared role.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point — route + call ChatGPT + return answer |
| `router_rules.py` | Keyword scoring + drift detection |
| `cordelia.identity.yaml` | Cordelia role constraints |
| `starhawk.identity.yaml` | Starhawk role constraints |
| `checks/drift_keywords.json` | Out-of-role vocabulary flags |
| `boundaries.md` | Agent boundary rules |
