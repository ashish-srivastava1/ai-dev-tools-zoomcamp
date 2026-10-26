import agent_runner


def test_allowed_tools_default_has_tests_but_no_git(monkeypatch):
    monkeypatch.delenv("ONCALL_GIT", raising=False)
    monkeypatch.delenv("CLAUDE_ALLOWED_TOOLS", raising=False)
    tools = agent_runner.allowed_tools()
    assert "Bash(uv run pytest:*)" in tools
    assert not any(t.startswith("Bash(git") for t in tools)


def test_allowed_tools_git_when_enabled(monkeypatch):
    monkeypatch.setenv("ONCALL_GIT", "1")
    monkeypatch.delenv("CLAUDE_ALLOWED_TOOLS", raising=False)
    assert "Bash(gh:*)" in agent_runner.allowed_tools()


def test_allowed_tools_override(monkeypatch):
    monkeypatch.setenv("CLAUDE_ALLOWED_TOOLS", "Read Bash(make:*)")
    assert agent_runner.allowed_tools() == ["Read", "Bash(make:*)"]
