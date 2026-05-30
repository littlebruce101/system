import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from router_rules import route_request, check_drift, route_and_check, load_drift_rules


# ---------------------------------------------------------------------------
# route_request
# ---------------------------------------------------------------------------

class TestRouteRequest:
    def test_cordelia_keywords_route_to_cordelia(self):
        assert route_request("I feel overwhelmed and scared") == "cordelia"

    def test_starhawk_keywords_route_to_starhawk(self):
        assert route_request("What are my options before the deadline?") == "starhawk"

    def test_tie_routes_to_mediator(self):
        # "feel" → cordelia, "plan" → starhawk: equal scores
        assert route_request("I feel like I need a plan") == "mediator"

    def test_empty_prompt_returns_mediator(self):
        assert route_request("") == "mediator"

    def test_whitespace_only_returns_mediator(self):
        assert route_request("   ") == "mediator"

    def test_no_known_keywords_returns_mediator(self):
        assert route_request("hello world") == "mediator"

    def test_case_insensitive_cordelia(self):
        assert route_request("I FEEL LOST AND HURT") == "cordelia"

    def test_case_insensitive_starhawk(self):
        assert route_request("MAP OUT THE RISK AND TIMELINE") == "starhawk"

    def test_multiple_cordelia_keywords_win(self):
        # breathe, feel, grieve vs plan
        assert route_request("I need to breathe, I feel lost, I grieve, I need a plan") == "cordelia"

    def test_multiple_starhawk_keywords_win(self):
        # map, risk, deadline, plan vs feel
        assert route_request("I feel uncertain but map the risk, set a deadline, and plan") == "starhawk"

    def test_substring_matching_inside_word(self):
        # "risk" is inside "risky" — current logic uses `in` so this will match
        result = route_request("this feels risky")
        # "feel" matches cordelia, "risk" substring in "risky" matches starhawk → tie → mediator
        assert result == "mediator"


# ---------------------------------------------------------------------------
# load_drift_rules
# ---------------------------------------------------------------------------

class TestLoadDriftRules:
    def test_returns_dict_when_file_exists(self, tmp_path):
        rules = {"cordelia_flags": ["deadline"], "starhawk_flags": ["breathe"]}
        drift_file = tmp_path / "drift_keywords.json"
        drift_file.write_text(json.dumps(rules))

        with patch("router_rules.DRIFT_FILE", drift_file):
            result = load_drift_rules()

        assert result == rules

    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        with patch("router_rules.DRIFT_FILE", missing):
            result = load_drift_rules()
        assert result == {}

    def test_returns_empty_dict_disables_drift_checks(self, tmp_path):
        missing = tmp_path / "nonexistent.json"
        with patch("router_rules.DRIFT_FILE", missing):
            flags = check_drift("cordelia", "deadline and timeline")
        assert flags == []


# ---------------------------------------------------------------------------
# check_drift
# ---------------------------------------------------------------------------

SAMPLE_DRIFT_RULES = {
    "cordelia_flags": ["branch", "deadline", "timeline", "risk window"],
    "starhawk_flags": ["breathe", "felt sense", "self-soothe", "hug", "tend", "grieve"],
}


class TestCheckDrift:
    @pytest.fixture(autouse=True)
    def patch_drift_rules(self):
        with patch("router_rules.load_drift_rules", return_value=SAMPLE_DRIFT_RULES):
            yield

    def test_detects_single_drift_flag(self):
        flags = check_drift("cordelia", "let me show you the timeline")
        assert "timeline" in flags

    def test_detects_multiple_drift_flags(self):
        flags = check_drift("cordelia", "check the deadline and the branch")
        assert set(flags) == {"deadline", "branch"}

    def test_returns_empty_when_no_drift(self):
        flags = check_drift("cordelia", "I hear you, that sounds hard")
        assert flags == []

    def test_case_insensitive_flag_detection(self):
        flags = check_drift("cordelia", "DEADLINE approaching fast")
        assert "deadline" in flags

    def test_starhawk_drift_detected(self):
        flags = check_drift("starhawk", "maybe you need to breathe and grieve")
        assert "breathe" in flags
        assert "grieve" in flags

    def test_unknown_agent_returns_empty(self):
        # "mediator_flags" key does not exist in the rules
        flags = check_drift("mediator", "deadline breathe timeline")
        assert flags == []

    def test_multi_word_flag_detected(self):
        flags = check_drift("cordelia", "there is a real risk window here")
        assert "risk window" in flags

    def test_multi_word_flag_not_falsely_triggered(self):
        flags = check_drift("cordelia", "there is some risk here")
        assert "risk window" not in flags


# ---------------------------------------------------------------------------
# route_and_check
# ---------------------------------------------------------------------------

class TestRouteAndCheck:
    @pytest.fixture(autouse=True)
    def patch_drift_rules(self):
        with patch("router_rules.load_drift_rules", return_value=SAMPLE_DRIFT_RULES):
            yield

    def test_result_has_required_keys(self):
        result = route_and_check("I feel lost")
        assert set(result.keys()) == {"agent", "cordelia_signals", "starhawk_signals", "drift_flags"}

    def test_correct_agent_assigned(self):
        result = route_and_check("I feel overwhelmed and scared")
        assert result["agent"] == "cordelia"

    def test_signal_lists_contain_matched_keywords(self):
        result = route_and_check("I feel lost and need a plan")
        assert "feel" in result["cordelia_signals"]
        assert "lost" in result["cordelia_signals"]
        assert "plan" in result["starhawk_signals"]

    def test_no_response_skips_drift_check(self):
        result = route_and_check("I feel lost")
        assert result["drift_flags"] == []

    def test_empty_response_skips_drift_check(self):
        result = route_and_check("I feel lost", response="")
        assert result["drift_flags"] == []

    def test_drift_detected_when_response_provided(self):
        result = route_and_check("I feel overwhelmed", response="let me show you the deadline")
        assert "deadline" in result["drift_flags"]

    def test_no_drift_when_response_is_clean(self):
        result = route_and_check("I feel overwhelmed", response="I hear you, that sounds really hard")
        assert result["drift_flags"] == []

    def test_tie_routes_to_mediator_with_no_signals(self):
        result = route_and_check("hello world")
        assert result["agent"] == "mediator"
        assert result["cordelia_signals"] == []
        assert result["starhawk_signals"] == []
