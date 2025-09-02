from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / ".github" / "workflows"


def _load_yaml(path: Path) -> dict:
    assert path.is_file(), f"Missing workflow: {path}"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_on_block(data: dict) -> dict:
    """
    GitHub uses 'on' as a key, but YAML 1.1 may parse unquoted 'on' as True.
    Accept either 'on' or True as the trigger map.
    """
    if "on" in data and data["on"]:
        return data["on"] or {}
    if True in data and data[True]:
        # unquoted 'on:' parsed as True
        return data[True] or {}
    return {}


def _branches_value(hook: dict, key: str) -> list[str]:
    """
    Normalize 'branches' / 'branches-ignore' to a list of strings.
    """
    if not isinstance(hook, dict):
        return []
    val = hook.get(key, [])
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return val
    return []


def _tags_value(hook: dict) -> list[str]:
    """
    Normalize push.tags to a list of strings.
    """
    if not isinstance(hook, dict):
        return []
    val = hook.get("tags", [])
    if isinstance(val, str):
        return [val]
    if isinstance(val, list):
        return val
    return []


def test_workflow_files_exist():
    required = ["ci-pr.yml", "ci-push.yml", "ci-tag.yml", "commitlint.yml", "smoke.yml"]
    missing = [name for name in required if not (WF / name).is_file()]
    assert not missing, f"Missing workflow file(s): {', '.join(missing)}"


def test_workflow_names_are_expected():
    expected_names = {
        "ci-pr.yml": "CI-CD PR",
        "ci-push.yml": "CI-CD Push",
        "ci-tag.yml": "CI-CD Tag",
        "commitlint.yml": "commitlint",
        "smoke.yml": "smoke",
    }
    for fname, expected in expected_names.items():
        data = _load_yaml(WF / fname)
        actual = data.get("name")
        assert actual == expected, f"{fname}: expected name='{expected}', got '{actual}'"


def test_ci_pr_triggers_on_prs_to_main_or_env_test():
    data = _load_yaml(WF / "ci-pr.yml")
    on = _get_on_block(data)
    pr = on.get("pull_request") or {}
    branches = set(_branches_value(pr, "branches"))
    want = {"main", "env-test"}
    assert branches & want, f"ci-pr.yml: pull_request.branches must include 'main' or 'env-test' (got {sorted(branches)})"


def test_ci_push_triggers_on_push_to_main_or_env_test():
    data = _load_yaml(WF / "ci-push.yml")
    on = _get_on_block(data)
    push = on.get("push") or {}
    branches = set(_branches_value(push, "branches"))
    want = {"main", "env-test"}
    assert branches & want, f"ci-push.yml: push.branches must include 'main' or 'env-test' (got {sorted(branches)})"


def test_smoke_triggers_ignore_main_and_env_test():
    data = _load_yaml(WF / "smoke.yml")
    on = _get_on_block(data)

    push = on.get("push") or {}
    push_ignored = set(_branches_value(push, "branches-ignore"))
    for b in ("main", "env-test"):
        assert b in push_ignored, f"smoke.yml: push.branches-ignore must include '{b}' (got {sorted(push_ignored)})"

    pr = on.get("pull_request") or {}
    pr_ignored = set(_branches_value(pr, "branches-ignore"))
    for b in ("main", "env-test"):
        assert b in pr_ignored, f"smoke.yml: pull_request.branches-ignore must include '{b}' (got {sorted(pr_ignored)})"


def test_commitlint_is_branch_agnostic():
    data = _load_yaml(WF / "commitlint.yml")
    on = _get_on_block(data)
    assert on, "commitlint.yml: expected a non-empty 'on' section"


def test_ci_tag_triggers_on_version_tags():
    data = _load_yaml(WF / "ci-tag.yml")
    on = _get_on_block(data)
    push = on.get("push") or {}
    tags = _tags_value(push)
    assert tags, "ci-tag.yml: expected push.tags to be defined (e.g., ['v*.*.*'])"
