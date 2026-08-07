"""Architectural constraints, enforced instead of documented.

The package is a library with a thin command layer on top — `__init__` calls it
"CLI and Python client". That claim is only true while nothing below `cli/`
reaches for typer or writes to stdout, and it is exactly the kind of rule that
decays silently: one `print()` added for debugging, and a library function stops
being usable from a notebook without anything failing.

So the rules are AST-checked rather than reviewed. All three are cheap; the
alternative is finding out when someone's script prints to their terminal.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "tamarind"
CLI_DIR = SRC / "cli"


def _library_modules() -> list[Path]:
    """Every module in the package EXCEPT the command layer."""
    return sorted(p for p in SRC.rglob("*.py") if CLI_DIR not in p.parents and p != CLI_DIR)


def _imported_names(tree: ast.AST) -> set[str]:
    """Top-level module names this file imports, absolute imports only.

    Relative imports (`from .plan import x`) carry no module name in `node.module`
    for level>0 in the way we care about here, so they are resolved separately by
    `_relative_targets`.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def _relative_targets(tree: ast.AST) -> set[str]:
    """Module names reached by a relative import, e.g. `from .api import x` -> {'api'}."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level and node.module:
            out.add(node.module.split(".")[0])
        # `from . import api` — the target is in the alias list, not `node.module`.
        if isinstance(node, ast.ImportFrom) and node.level and node.module is None:
            out.update(a.name.split(".")[0] for a in node.names)
    return out


def _calls_named(tree: ast.AST, fname: str) -> bool:
    return any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == fname
        for n in ast.walk(tree)
    )


@pytest.mark.parametrize("path", _library_modules(), ids=lambda p: str(p.name))
def test_library_does_not_import_the_command_framework(path: Path) -> None:
    """No typer below `cli/`.

    This is the load-bearing one: it is what makes "the SDK is the same code" true
    rather than aspirational. A library function that raises `typer.Exit` or reads a
    typer context cannot be called from a script.
    """
    tree = ast.parse(path.read_text())
    assert "typer" not in _imported_names(tree), f"{path.name} imports typer; it belongs under cli/"
    assert "click" not in _imported_names(tree), f"{path.name} imports click; it belongs under cli/"


@pytest.mark.parametrize("path", _library_modules(), ids=lambda p: str(p.name))
def test_library_does_not_write_to_stdout(path: Path) -> None:
    """No `print()` below `cli/` — progress is reported through callbacks.

    A library that prints is unusable from a notebook and corrupts `--json` output
    when its text lands on stdout alongside the result object.
    """
    tree = ast.parse(path.read_text())
    assert not _calls_named(tree, "print"), f"{path.name} calls print(); emit an event instead"


@pytest.mark.parametrize(
    "path",
    [p for p in _library_modules() if p.name == "plan.py"],
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_plan_modules_are_pure(path: Path) -> None:
    """`plan.py` holds decisions, not I/O — so it may not reach the network or the clock.

    This is what makes the interesting logic testable without a server: a decision
    that cannot perform I/O can be exercised as a table of inputs and outputs. The
    moment a plan module imports the api layer, its tests start needing fixtures.
    """
    tree = ast.parse(path.read_text())
    absolute = _imported_names(tree)
    relative = _relative_targets(tree)
    for forbidden in ("api", "flow", "http"):
        assert forbidden not in relative, f"{path} imports {forbidden}; plan must stay pure"
    for forbidden in ("httpx", "requests"):
        assert forbidden not in absolute, f"{path} imports {forbidden}; plan must stay pure"


# Errors that deliberately carry the generic code. APIError is the catch-all for a
# non-2xx that maps to nothing more specific, so exit 1 IS its answer.
_GENERIC_BY_DESIGN = {"APIError"}


def _all_error_subclasses() -> set[type]:
    from tamarind import errors

    found: set[type] = set()
    stack = [errors.TamarindError]
    while stack:
        for sub in stack.pop().__subclasses__():
            if sub not in found:
                found.add(sub)
                stack.append(sub)
    return found


def test_every_error_declares_a_known_exit_code() -> None:
    """Exit codes are a documented contract agents branch on, so every error needs one.

    The failure this catches is quiet: `exit_code` is inherited, so a new subclass that
    forgets to declare one silently reports the generic failure code, and a caller
    branching on it cannot tell the new condition from an unexpected crash.
    """
    from tamarind import errors

    declared = {v for k, v in vars(errors.ExitCode).items() if isinstance(v, int)}
    for exc in _all_error_subclasses():
        assert exc.exit_code in declared, (
            f"{exc.__name__}.exit_code = {exc.exit_code} is not a value on ExitCode"
        )
        if exc.__name__ not in _GENERIC_BY_DESIGN:
            assert exc.exit_code != errors.ExitCode.ERROR, (
                f"{exc.__name__} inherits the generic ERROR code. Declare one on the class, "
                f"or add it to _GENERIC_BY_DESIGN with a reason."
            )


def test_exit_codes_are_distinct() -> None:
    """Two conditions sharing a code makes the code useless for branching."""
    from tamarind import errors

    codes = [v for k, v in vars(errors.ExitCode).items() if isinstance(v, int)]
    assert len(codes) == len(set(codes)), "duplicate ExitCode values"
