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

DRIFT_ESCALATION_THRESHOLD = 3


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


class DriftSession:
    """Tracks accumulated drift flags across multiple turns in a session.

    When an agent accumulates DRIFT_ESCALATION_THRESHOLD or more drift flags,
    subsequent routing for that agent is escalated to Mediator.
    """

    def __init__(self):
        self._counts: dict[str, int] = {}
        self._all_flags: dict[str, list[str]] = {}

    def record(self, agent: str, flags: list[str]) -> None:
        self._counts[agent] = self._counts.get(agent, 0) + len(flags)
        self._all_flags.setdefault(agent, []).extend(flags)

    def should_escalate(self, agent: str) -> bool:
        return self._counts.get(agent, 0) >= DRIFT_ESCALATION_THRESHOLD

    def summary(self) -> dict:
        return {
            agent: {"count": self._counts[agent], "flags": self._all_flags[agent]}
            for agent in self._counts
        }


def route_and_check(prompt: str, response: str = "", session: DriftSession | None = None) -> dict:
    """
    Route a prompt and optionally check a response for drift.

    If a DriftSession is provided, drift flags are accumulated across calls.
    Once an agent reaches DRIFT_ESCALATION_THRESHOLD flags, routing escalates
    to mediator for review.

    Returns a result dict with agent, confidence signals, drift flags, and
    an escalated flag when the session threshold has been exceeded.
    """
    prompt_lower = prompt.lower()
    cordelia_hits = [w for w in ROUTING_RULES["cordelia"] if w in prompt_lower]
    starhawk_hits = [w for w in ROUTING_RULES["starhawk"] if w in prompt_lower]
    agent = route_request(prompt)

    drift_flags = check_drift(agent, response) if response else []
    escalated = False

    if session is not None:
        if drift_flags:
            session.record(agent, drift_flags)
        if session.should_escalate(agent):
            agent = "mediator"
            escalated = True

    result = {
        "agent": agent,
        "cordelia_signals": cordelia_hits,
        "starhawk_signals": starhawk_hits,
        "drift_flags": drift_flags,
        "escalated": escalated,
    }
    return result


def session_close(session: DriftSession) -> dict:
    """
    Perform end-of-session role checks as required by boundary rules.

    Returns a report indicating whether each agent stayed within its role.
    An agent fails the check if it accumulated any drift flags during the session.
    """
    summary = session.summary()
    checks = {
        "cordelia": "did not predict or plan strategically",
        "starhawk": "did not soothe or do emotional caretaking",
    }
    report = {}
    for agent, assertion in checks.items():
        drift_count = summary.get(agent, {}).get("count", 0)
        report[agent] = {
            "passed": drift_count == 0,
            "assertion": assertion,
            "drift_count": drift_count,
        }
    return report


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
    if result["escalated"]:
        print("Escalated to Mediator (drift threshold reached)")
