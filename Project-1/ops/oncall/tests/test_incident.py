import datetime as dt

import incident as inc
from tests.conftest import firing


def test_parse_grafana_payload():
    [a] = inc.parse_alerts(firing())
    assert a.status == "firing" and a.alertname == "LearnLoop key journey 5xx"
    assert a.endpoint == "GET /api/dashboard" and not a.is_test
    assert a.key == "LearnLoop key journey 5xx:fp1"


def test_detects_test_alerts():
    p = firing(alertname="TestAlert")
    assert inc.parse_alerts(p)[0].is_test
    p = firing()
    p["alerts"][0]["labels"]["test"] = "true"
    assert inc.parse_alerts(p)[0].is_test


def test_fingerprint_fallback_is_stable():
    p = firing()
    del p["alerts"][0]["fingerprint"]
    assert inc.parse_alerts(p)[0].fingerprint == inc.parse_alerts(p)[0].fingerprint


def test_dedupe_window():
    [a] = inc.parse_alerts(firing())
    now = dt.datetime(2026, 10, 26, 10, tzinfo=dt.UTC)
    seen = {a.key: now - dt.timedelta(minutes=5)}
    assert inc.is_duplicate(seen, a, now, 15)
    assert not inc.is_duplicate(seen, a, now, 3)
    assert not inc.is_duplicate({}, a, now, 15)


def test_prompt_contains_evidence_and_steps():
    [a] = inc.parse_alerts(firing())
    ctx = {"metric": {"x": 1}, "logs": {"lines": ["ZeroDivisionError"]}, "traces": {}}
    p = inc.build_prompt(a, ctx, "/repo", "INC1", git_enabled=False)
    for needle in ("GET /api/dashboard", "ZeroDivisionError", "AGENTS.md", "ops/runbook.md",
                   "failing unit test", "uv run pytest", "Git is DISABLED"):
        assert needle in p
    assert "gh pr create" not in p


def test_prompt_git_steps_only_when_enabled():
    [a] = inc.parse_alerts(firing())
    p = inc.build_prompt(a, {}, "/repo", "INC1", git_enabled=True)
    assert "fix/oncall-INC1" in p and "type:bug,area:ops,project-1" in p and "Closes #" in p


def test_test_prompt_takes_no_action():
    [a] = inc.parse_alerts(firing(alertname="TestAlert"))
    assert "no action was required" in inc.build_prompt(a, {}, "/r", "I", True).lower()


def test_prompt_truncates_huge_evidence():
    [a] = inc.parse_alerts(firing())
    p = inc.build_prompt(a, {"logs": {"lines": ["x" * 50000]}}, "/r", "I", False)
    assert "[truncated]" in p and len(p) < 20000
