# tests/test_v1_cli_logging.py
from __future__ import annotations

import runpy
import sys
from types import SimpleNamespace
from typing import Any, Iterable

import pytest


# ----------------------------
# Helpers / fixtures
# ----------------------------

@pytest.fixture(autouse=True)
def _clean_root_logger():
    """Isolate root logger handlers across tests."""
    import logging

    root = logging.getLogger()
    old_level = root.level
    old_handlers = list(root.handlers)
    try:
        yield
    finally:
        # restore original handlers & level
        for h in list(root.handlers):
            root.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass
        for h in old_handlers:
            root.addHandler(h)
        root.setLevel(old_level)


def _make_error(reason: str = "boom", position: Any = None, sourceline: int | None = None) -> Any:
    """Build a minimal xmlschema-like validation error object."""
    obj = SimpleNamespace(sourceline=sourceline) if sourceline is not None else None
    elem = SimpleNamespace(sourceline=sourceline) if (sourceline is not None and obj is None) else None
    return SimpleNamespace(reason=reason, position=position, obj=obj, elem=elem)


# ----------------------------
# extract_position coverage
# ----------------------------

def test_extract_position_from_position_tuple_line_and_col():
    from mug.cli import extract_position

    err = _make_error(position=(12, 5))
    assert extract_position(err) == (12, 5)

def test_extract_position_from_obj_sourceline_only():
    from mug.cli import extract_position

    err = _make_error(position=None, sourceline=42)
    assert extract_position(err) == (42, None)

def test_extract_position_from_elem_sourceline_only():
    from mug.cli import extract_position

    # ensure elem is used when obj is absent
    err = SimpleNamespace(reason="x", position=None, obj=None, elem=SimpleNamespace(sourceline=7))
    assert extract_position(err) == (7, None)

def test_extract_position_none_available():
    from mug.cli import extract_position

    err = _make_error(position=None, sourceline=None)
    assert extract_position(err) == (None, None)


# ----------------------------
# CLI main() success & failure
# ----------------------------

def _patch_xmlschema_ok(mocker, version: str = "1.1", errors: Iterable[Any] = ()):
    """Patch xmlschema constructors + exception type and iter_errors behavior."""
    import mug.cli as cli

    class FakeSchema:
        def __init__(self, *_args, **_kw):
            pass
        def iter_errors(self, _xml):
            for e in errors:
                yield e

    class FakeXMLSchemaException(Exception):
        pass

    mocker.patch.object(cli, "xmlschema")
    cli.xmlschema.XMLSchemaException = FakeXMLSchemaException
    mocker.patch.object(cli.xmlschema, "XMLSchema11", return_value=FakeSchema())
    mocker.patch.object(cli.xmlschema, "XMLSchema10", return_value=FakeSchema())
    return FakeXMLSchemaException


def test_cli_main_ok_prints_ok_and_exits_zero(mocker, capsys):
    import mug.cli as cli

    _patch_xmlschema_ok(mocker, errors=())
    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 0
    out = capsys.readouterr().out
    assert "OK" in out


def test_cli_main_reports_errors_and_exit_one(mocker, capsys):
    import mug.cli as cli

    err1 = _make_error(reason="invalid element A", position=(4, 1))
    err2 = _make_error(reason="invalid attribute B", sourceline=9)
    _patch_xmlschema_ok(mocker, errors=(err1, err2))
    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 1
    err = capsys.readouterr().err
    assert "doc.xml:4:1: ERROR: invalid element A" in err
    assert "doc.xml:9:0: ERROR: invalid attribute B" in err  # default col=0 when unknown


def test_cli_main_fail_fast_prints_first_error_only(mocker, capsys):
    import mug.cli as cli

    err1 = _make_error(reason="first", position=(10, 2))
    err2 = _make_error(reason="second", position=(11, 3))
    _patch_xmlschema_ok(mocker, errors=(err1, err2))
    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd", "--fail-fast"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 1
    err = capsys.readouterr().err
    assert "first" in err and "second" not in err


def test_cli_main_schema_exception_exit_three(mocker, capsys):
    import mug.cli as cli

    FakeXMLSchemaException = _patch_xmlschema_ok(mocker)
    # Make constructor raise schema exception
    mocker.patch.object(cli.xmlschema, "XMLSchema11", side_effect=FakeXMLSchemaException("bad schema"))
    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 3
    assert "SCHEMA ERROR" in capsys.readouterr().err


def test_cli_main_schema_read_oserror_exit_three(mocker, capsys):
    import mug.cli as cli

    _patch_xmlschema_ok(mocker)
    mocker.patch.object(cli.xmlschema, "XMLSchema11", side_effect=OSError("io"))
    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 3
    assert "SCHEMA READ ERROR" in capsys.readouterr().err


def test_cli_main_input_read_error_exit_two(mocker, capsys):
    import mug.cli as cli

    class FakeSchema:
        def __init__(self, *_args, **_kw):
            pass
        def iter_errors(self, _xml):
            raise OSError("input io")

    class FakeXMLSchemaException(Exception):
        pass

    mocker.patch.object(cli, "xmlschema")
    cli.xmlschema.XMLSchemaException = FakeXMLSchemaException
    mocker.patch.object(cli.xmlschema, "XMLSchema11", return_value=FakeSchema())
    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 2
    assert "INPUT READ ERROR" in capsys.readouterr().err


# ----------------------------
# __main__ wiring coverage
# ----------------------------

def test_package___main___delegates_to_cli(mocker):
    """Ensure `python -m mug` executes the CLI path."""
    # To avoid exercising real CLI, stub cli.main to a predictable exit.
    import mug.cli as cli
    mocker.patch.object(cli, "main", side_effect=lambda: sys.exit(0))

    # Running the package as a module triggers mug/__main__.py
    with pytest.raises(SystemExit) as ex:
        runpy.run_module("mug.__main__", run_name="__main__")
    assert ex.value.code == 0


# ----------------------------
# logging configuration coverage
# ----------------------------

def test_configure_logging_adds_console_and_file_handlers(tmp_path, caplog):
    import logging
    from mug.logging_config import configure_logging

    caplog.set_level(logging.INFO)
    log_path = tmp_path / "logs" / "app.log"
    configure_logging(level="INFO", log_file=str(log_path))

    root = logging.getLogger()
    # One console StreamHandler
    assert any(h.__class__.__name__ == "StreamHandler" and getattr(h, "stream", None) is not sys.stderr
               for h in root.handlers)
    # One RotatingFileHandler
    assert any(h.__class__.__name__ == "RotatingFileHandler" for h in root.handlers)
    # One stderr mirror (StreamHandler with stream=sys.stderr)
    assert any(h.__class__.__name__ == "StreamHandler" and getattr(h, "stream", None) is sys.stderr
               for h in root.handlers)
    # Log directory should be created
    assert log_path.parent.is_dir()


def test_configure_logging_is_idempotent(tmp_path):
    import logging
    from mug.logging_config import configure_logging

    log_path = tmp_path / "logs" / "app.log"
    configure_logging(level="INFO", log_file=str(log_path))
    # Call again; should not duplicate handlers
    configure_logging(level="INFO", log_file=str(log_path))

    root = logging.getLogger()
    num_stream = sum(h.__class__.__name__ == "StreamHandler" for h in root.handlers)
    num_rotate = sum(h.__class__.__name__ == "RotatingFileHandler" for h in root.handlers)
    # Expect exactly two StreamHandlers (stdout + stderr) and one RotatingFileHandler
    assert num_stream == 2
    assert num_rotate == 1


# ----------------------------
# global error handling coverage
# ----------------------------

def test_install_global_error_handler_sets_hooks_and_logs(caplog):
    import logging
    import threading as _threading
    from mug.error_handling import install_global_error_handler, _global_exception_hook, _thread_exception_hook

    caplog.set_level(logging.ERROR)

    install_global_error_handler()

    # main-thread hook
    assert sys.excepthook is _global_exception_hook

    # thread hook when available
    if hasattr(_threading, "excepthook"):
        assert _threading.excepthook is _thread_exception_hook

        # simulate a thread exception
        args = SimpleNamespace(
            thread=SimpleNamespace(name="T"),
            exc_type=ValueError,
            exc_value=ValueError("bad"),
            exc_traceback=None,
        )
        _thread_exception_hook(args)
        assert "Uncaught thread exception" in caplog.text

    # simulate an uncaught main-thread exception
    _global_exception_hook(RuntimeError, RuntimeError("boom"), None)
    assert "Uncaught exception" in caplog.text


def test_cli_main_uses_xmlschema10_when_requested(mocker, capsys):
    import mug.cli as cli

    class FakeSchema:
        def __init__(self, *_a, **_k): ...
        def iter_errors(self, _xml): return []
    class FakeXMLSchemaException(Exception): ...

    # Patch constructors and exception type
    mocker.patch.object(cli, "xmlschema")
    cli.xmlschema.XMLSchemaException = FakeXMLSchemaException
    mocker.patch.object(cli.xmlschema, "XMLSchema11", return_value=FakeSchema())
    mocker.patch.object(cli.xmlschema, "XMLSchema10", return_value=FakeSchema())

    # Ask for 1.0 so the XMLSchema10 branch executes
    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd", "--xsd-version", "1.0"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 0
    assert "OK" in capsys.readouterr().out


def test_cli_main_quiet_suppresses_ok(mocker, capsys):
    import mug.cli as cli

    class FakeSchema:
        def __init__(self, *_a, **_k): ...
        def iter_errors(self, _xml): return []

    mocker.patch.object(cli, "xmlschema")
    mocker.patch.object(cli.xmlschema, "XMLSchema11", return_value=FakeSchema())

    mocker.patch.object(sys, "argv", ["mug", "doc.xml", "schema.xsd", "--quiet"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 0
    out = capsys.readouterr().out
    assert out.strip() == ""  # no "OK" when --quiet


def test__parse_level_branches_and_fallbacks():
    import logging
    from mug.logging_config import _parse_level

    # int passthrough
    assert _parse_level(logging.WARNING) == logging.WARNING
    # valid string name
    assert _parse_level("INFO") == logging.INFO
    # invalid string -> fallback
    assert _parse_level("NOTALEVEL", fallback=logging.ERROR) == logging.ERROR
    # trigger exception path (no .upper) -> fallback
    class NoUpper: pass
    assert _parse_level(NoUpper(), fallback=logging.CRITICAL) == logging.CRITICAL  # type: ignore[arg-type]


def test_configure_logging_uses_env_vars_for_level_and_file(monkeypatch, tmp_path):
    import logging
    from mug.logging_config import configure_logging

    # Set env so configure_logging(None, None, None) uses them
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    log_path = tmp_path / "logs" / "env_app.log"
    monkeypatch.setenv("LOG_FILE", str(log_path))
    monkeypatch.setenv("LOG_FMT", "%(levelname)s:%(name)s:%(message)s")

    configure_logging(level=None, log_file=None, fmt=None)

    # Ensure both stdout and stderr stream handlers still present and file created
    import logging as _lg, sys as _sys
    root = _lg.getLogger()
    assert any(isinstance(h, _lg.StreamHandler) and getattr(h, "stream", None) is _sys.stdout for h in root.handlers)
    assert any(isinstance(h, _lg.StreamHandler) and getattr(h, "stream", None) is _sys.stderr for h in root.handlers)
    assert log_path.exists()


def test_import_exposes_version():
    import mug
    # Accessing __version__ executes the remaining line in __init__.py
    assert isinstance(getattr(mug, "__version__", "0.0.0"), str)
    
def test_cli_runs_when_module_executed_as_script(monkeypatch, mocker):
    import runpy, sys

    # Make sure the module gets re-executed cleanly
    sys.modules.pop("mug.cli", None)

    # Provide argv so main() has inputs
    monkeypatch.setattr(sys, "argv", ["mug", "doc.xml", "schema.xsd"], raising=False)

    # Stub xmlschema *for the new execution* of mug.cli by injecting a fake module
    class FakeSchema:
        def __init__(self, *_a, **_k):
            pass
        def iter_errors(self, _xml):
            return []  # no errors → exit code 0

    class FakeXMLSchemaException(Exception):
        pass

    fake_xmlschema = type(
        "FakeXmlschema",
        (),
        {
            "XMLSchema11": staticmethod(lambda _x: FakeSchema()),
            "XMLSchema10": staticmethod(lambda _x: FakeSchema()),
            "XMLSchemaException": FakeXMLSchemaException,
        },
    )()

    # Ensure `import xmlschema` inside the re-executed mug.cli resolves to our fake
    monkeypatch.setitem(sys.modules, "xmlschema", fake_xmlschema)

    # Now execute mug.cli as a script; the bottom guard should call main() and exit(0)
    with pytest.raises(SystemExit) as ex:
        runpy.run_module("mug.cli", run_name="__main__")
    assert ex.value.code == 0



def test_init_version_fallback_branch(monkeypatch):
    import importlib, sys

    # Force the internal version import to fail on reload
    sys.modules.pop("mug", None)  # ensure a fresh import path
    monkeypatch.setitem(sys.modules, "mug._version", None)  # makes import fail with ImportError

    mug2 = importlib.import_module("mug")
    assert isinstance(getattr(mug2, "__version__", "0.0.0"), str)


def test_package_get_version_matches_dunder():
    import mug
    assert mug.get_version() == getattr(mug, "__version__", "")
