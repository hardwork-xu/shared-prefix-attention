"""Real temporary Git identity regressions. / 使用临时 Git 仓库测试提交身份预检。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit import audit, precommit_identity

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ADDRESS = "fixture-maintainer" + "@users.noreply.github.com"
PRIVATE_ADDRESS = "fixture-private" + "@" + "example.invalid"


@pytest.fixture
def identity_repo(tmp_path, monkeypatch):
    # Isolate test identity from host config and inherited CI variables.
    # 将测试身份与宿主机配置、继承的 CI 环境变量隔离。
    for name in tuple(os.environ):
        if name.startswith("GIT_") or name == "EMAIL":
            monkeypatch.delenv(name, raising=False)
    global_config = tmp_path / "empty-gitconfig"
    global_config.touch()
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
    for key, value in (("user.name", "Fixture Maintainer"), ("user.email", PUBLIC_ADDRESS)):
        subprocess.run(["git", "config", "--local", key, value], cwd=root, check=True)
    return root


def test_safe_effective_identity_and_cli(identity_repo):
    result = precommit_identity(identity_repo)
    assert result["status"] == "passed" and result["identities_checked"] == 2
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/audit.py"),
            "--root",
            str(identity_repo),
            "--precommit-identity",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0
    assert json.loads(process.stdout)["git_history_status"] == "not_checked_by_precommit_mode"
    assert PUBLIC_ADDRESS not in process.stdout + process.stderr


def test_unsafe_config_rejected_without_disclosure(identity_repo):
    subprocess.run(
        ["git", "config", "--local", "user.email", PRIVATE_ADDRESS], cwd=identity_repo, check=True
    )
    result = precommit_identity(identity_repo)
    assert result["status"] == "failed"
    assert {finding["rule"] for finding in result["findings"]} == {
        "private-author-email",
        "private-committer-email",
    }
    assert PRIVATE_ADDRESS not in json.dumps(result)


@pytest.mark.parametrize("role", ["AUTHOR", "COMMITTER"])
def test_unsafe_environment_override_rejected(identity_repo, monkeypatch, role):
    monkeypatch.setenv(f"GIT_{role}_EMAIL", PRIVATE_ADDRESS)
    result = precommit_identity(identity_repo)
    assert result["status"] == "failed"
    assert [finding["rule"] for finding in result["findings"]] == [f"private-{role.lower()}-email"]
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/audit.py"),
            "--root",
            str(identity_repo),
            "--precommit-identity",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 1
    assert PRIVATE_ADDRESS not in process.stdout + process.stderr


def test_unavailable_identity_fails_closed(identity_repo):
    subprocess.run(["git", "config", "--unset", "user.email"], cwd=identity_repo, check=True)
    subprocess.run(["git", "config", "user.useConfigOnly", "true"], cwd=identity_repo, check=True)
    result = precommit_identity(identity_repo)
    assert result["status"] == "failed"
    assert {finding["rule"] for finding in result["findings"]} == {
        "unavailable-author-identity",
        "unavailable-committer-identity",
    }


def test_safe_preflight_does_not_clear_historical_finding(identity_repo, monkeypatch):
    with monkeypatch.context() as override:
        override.setenv("GIT_AUTHOR_EMAIL", PRIVATE_ADDRESS)
        override.setenv("GIT_COMMITTER_EMAIL", PRIVATE_ADDRESS)
        subprocess.run(
            ["git", "commit", "--quiet", "--allow-empty", "-m", "test: identity fixture"],
            cwd=identity_repo,
            check=True,
            capture_output=True,
        )
    assert precommit_identity(identity_repo)["status"] == "passed"
    result = audit(identity_repo)
    assert result["status"] == "failed" and result["commits_checked"] == 1
    assert {finding["rule"] for finding in result["findings"]} == {
        "private-author-email",
        "private-committer-email",
    }
    assert PRIVATE_ADDRESS not in json.dumps(result)


def test_nonrepository_rejected(tmp_path):
    assert precommit_identity(tmp_path)["status"] == "failed"
