from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_workflow_files_exist():
    required = [
        ".github/workflows/ci-pr.yml",
        ".github/workflows/ci-push.yml",
        ".github/workflows/ci-tag.yml",
    ]
    missing = [p for p in required if not (ROOT / p).is_file()]
    assert not missing, f"Missing workflow file(s): {', '.join(missing)}"
