from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_required_config_files_exist():
    must_exist = [
        "config/node/commitlint.config.js",
        "config/node/conventional-changelogrc.js",
        ".coveragerc",
        ".npmrc",
        "MANIFEST.in",
        "mypy.ini",
        "package.json",
        "package-lock.json",
        "pyproject.toml",
        "pytest.ini",
        "ruff.toml",
        ".gitignore",
        ".gitattributes",
        ".importlinter",
    ]
    missing = [p for p in must_exist if not (ROOT / p).exists()]
    assert not missing, f"Missing required file(s): {', '.join(missing)}"


def test_requirements_txt_does_not_exist_in_root():
    assert not (ROOT / "requirements.txt").exists(), "requirements.txt must NOT exist at repo root"


