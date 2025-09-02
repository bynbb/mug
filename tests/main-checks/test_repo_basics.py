from pathlib import Path

# Project root is two levels up from this file
ROOT = Path(__file__).resolve().parents[2]


def test_license_and_readme_exist():
    assert (ROOT / "LICENSE").is_file(), "Missing LICENSE at repo root"
    assert (ROOT / "README.md").is_file(), "Missing README.md at repo root"


def test_docs_policy_files_exist():
    docs = ROOT / "docs"
    assert docs.is_dir(), "Missing docs/ directory"
    required = ["TESTING_POLICY.md", "CONTRIBUTING.md", "CHANGELOG.md"]
    missing = [p for p in required if not (docs / p).is_file()]
    assert not missing, f"Missing in docs/: {', '.join(missing)}"
