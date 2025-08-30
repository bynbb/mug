import shutil, subprocess, shlex

def run(cmd: str):
    return subprocess.run(shlex.split(cmd), check=True, capture_output=True, text=True)

def _assert_docker_ready() -> None:
    if shutil.which("docker") is None:
        raise AssertionError("docker CLI not found on PATH.")
    subprocess.run(["docker", "info"], check=True, capture_output=True, text=True)

def test_build_and_run_cli_help():
    _assert_docker_ready()
    run("docker build -t mug/dev:local -f docker/Dockerfile .")
    out = run("docker run --rm mug/dev:local")
    assert out.stdout is not None and out.returncode == 0
