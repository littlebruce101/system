"""
agent_router.py — Keyword-based request routing between Cordelia and Starhawk.

Routes a prompt to the appropriate agent based on keyword signals.
Applies drift detection to flag when an agent response contains
vocabulary outside its declared role.

Usage:
    python router_rules.py "I feel overwhelmed and don't know what to do"
    python router_rules.py "What are my options before the deadline?"
"""

import json
import sys
from pathlib import Path


ROUTING_RULES = {
    "cordelia": ["breathe", "feel", "overwhelm", "comfort", "grief", "tender",
                 "scared", "lost", "hurt", "grieve"],
    "starhawk": ["map", "branch", "scenario", "option", "deadline", "horizon",
                 "risk", "plan", "decide", "timeline"],
}

DRIFT_FILE = Path(__file__).parent / "checks" / "drift_keywords.json"


def load_drift_rules() -> dict:
    if DRIFT_FILE.exists():
        return json.loads(DRIFT_FILE.read_text())
    return {}


def route_request(prompt: str) -> str:
    """Return the agent name best suited for this prompt."""
    prompt_lower = prompt.lower()
    cordelia_score = sum(1 for w in ROUTING_RULES["cordelia"] if w in prompt_lower)
    starhawk_score = sum(1 for w in ROUTING_RULES["starhawk"] if w in prompt_lower)

    if cordelia_score > starhawk_score:
        return "cordelia"
    elif starhawk_score > cordelia_score:
        return "starhawk"
    else:
        return "mediator"


def check_drift(agent: str, response: str) -> list[str]:
    """
    Return a list of drift flags found in the response.
    A drift flag means the agent used vocabulary outside its declared role.
    """
    drift_rules = load_drift_rules()
    flag_key = f"{agent}_flags"
    flags = drift_rules.get(flag_key, [])
    response_lower = response.lower()
    return [f for f in flags if f in response_lower]


def route_and_check(prompt: str, response: str = "") -> dict:
    """
    Route a prompt and optionally check a response for drift.
    Returns a result dict with agent, confidence signals, and any drift flags.
    """
    prompt_lower = prompt.lower()
    cordelia_hits = [w for w in ROUTING_RULES["cordelia"] if w in prompt_lower]
    starhawk_hits = [w for w in ROUTING_RULES["starhawk"] if w in prompt_lower]
    agent = route_request(prompt)

    result = {
        "agent": agent,
        "cordelia_signals": cordelia_hits,
        "starhawk_signals": starhawk_hits,
        "drift_flags": check_drift(agent, response) if response else [],
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python router_rules.py \"<prompt>\"")
        sys.exit(1)

    prompt = sys.argv[1]
    result = route_and_check(prompt)

    print(f"Agent:    {result['agent']}")
    print(f"Signals:  cordelia={result['cordelia_signals']}  starhawk={result['starhawk_signals']}")
    if result["drift_flags"]:
        print(f"Drift:    {result['drift_flags']}")
