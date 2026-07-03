from zero.cli.commands.pr import _parse_github_url, _parse_ai_pr_response

def test_parse_github_url():
    assert _parse_github_url("https://github.com/owner/repo.git") == "https://github.com/owner/repo"
    assert _parse_github_url("git@github.com:owner/repo.git") == "https://github.com/owner/repo"
    assert _parse_github_url("https://github.com/owner/repo") == "https://github.com/owner/repo"
    assert _parse_github_url("git@github.com:owner/repo") == "https://github.com/owner/repo"
    assert _parse_github_url("https://gitlab.com/owner/repo.git") is None

def test_parse_ai_pr_response():
    response = """
BRANCH: feat/add-logs-support
COMMIT: feat(cli): add logs support
TITLE: Add Logs Support
BODY:
This PR adds logs support to the CLI app.
- Implements logs
- Tests added
"""
    branch, commit, title, body = _parse_ai_pr_response(response)
    assert branch == "feat/add-logs-support"
    assert commit == "feat(cli): add logs support"
    assert title == "Add Logs Support"
    assert "This PR adds logs support" in body
