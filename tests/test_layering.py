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
    [p for p in _library_modules() if p.name in ("plan.py", "wire.py")],
    ids=lambda p: f"{p.parent.name}/{p.name}",
)
def test_decision_and_boundary_modules_are_pure(path: Path) -> None:
    """`plan` and `wire` hold decisions and parsing — never I/O.

    This is what makes the interesting logic testable without a server: a function
    that cannot perform I/O can be exercised as a table of inputs and outputs. The
    moment one of these imports the api layer, its tests start needing fixtures.

    `wire` is included because a parser that can fetch is no longer a boundary — it
    becomes a second, hidden client, and the shape knowledge stops being in one place.
    """
    tree = ast.parse(path.read_text())
    absolute = _imported_names(tree)
    relative = _relative_targets(tree)
    for forbidden in ("api", "flow", "http"):
        assert forbidden not in relative, f"{path} imports {forbidden}; it must stay pure"
    for forbidden in ("httpx", "requests"):
        assert forbidden not in absolute, f"{path} imports {forbidden}; it must stay pure"


def test_shape_knowledge_lives_only_at_the_boundary() -> None:
    """The API's key-casing variance is `wire`'s business and nobody else's.

    Before the boundary existed, the same "try JobName, then jobName, then name"
    walk appeared in several places and each copy had to be kept in step. Finding
    those spellings outside `wire` again means a second copy is forming.
    """
    offenders = []
    for path in _library_modules():
        if path.name == "wire.py":
            continue
        text = path.read_text()
        for spelling in ('"JobName"', '"batchStatus"', '"exampleJob"'):
            if spelling in text:
                offenders.append(f"{path.parent.name}/{path.name} contains {spelling}")
    assert not offenders, "shape knowledge outside wire.py: " + "; ".join(offenders)


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
