import shutil, subprocess, shlex
import pytest

def run(cmd: str, timeout: int = 600):
    # Force UTF-8 decoding and avoid failures on unrepresentable bytes from child processes.
    return subprocess.run(
        shlex.split(cmd),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )

def _assert_docker_ready() -> None:
    if shutil.which("docker") is None:
        pytest.skip("docker CLI not found on PATH")
    run("docker info")  # will raise if daemon is unhealthy

def test_build_and_run_cli_help():
    _assert_docker_ready()
    # Use host networking so the build phase can resolve/fetch python packages
    run("docker build --network=host -t mug/dev:local -f docker/Dockerfile .")
    out = run("docker run --rm mug/dev:local")
    assert out.returncode == 0
    assert out.stdout is not None and out.stdout.strip() != ""
