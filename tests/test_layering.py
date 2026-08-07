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


def _imported_components(tree: ast.AST) -> set[str]:
    """Every dotted component of every module this file imports.

    Keeping the FULL path matters. Reducing an import to its first component made
    `from tamarind.jobs.api import get_jobs` look like a plain `tamarind` import, so a
    plan module could depend on the api layer by spelling the import absolutely and
    the purity check would never see it. Components, not prefixes.

    Covers all three forms: ``import a.b``, ``from a.b import x``, ``from .b import x``
    and ``from . import b`` (whose target is in the alias list, not ``node.module``).
    """
    parts: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts.update(alias.name.split("."))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                parts.update(node.module.split("."))
            # Aliases count for EVERY from-import, relative or absolute. In
            # `from tamarind.jobs import api` the forbidden component is the alias,
            # not the module — reading only `node.module` misses it entirely.
            for alias in node.names:
                parts.update(alias.name.split("."))
    return parts


# What a pure module may not reach for. Internal I/O layers, network clients, and
# the CLOCK — the last one is not pedantry: `plan`/`wire` claim to be functions of
# their inputs, and a decision that reads the clock is not. It is also how a table
# test quietly turns into a flaky one.
_FORBIDDEN_IN_PURE = frozenset(
    {
        "api",  # the endpoint layer
        "flow",  # orchestration (which legitimately owns the clock)
        "http",  # this package's transport
        "httpx",  # network clients — third-party, stdlib and async
        "requests",
        "urllib",
        "aiohttp",
        "time",  # the clock
        "datetime",
        "pathlib",  # the filesystem
        "os",
        "io",
        "subprocess",
        "socket",
    }
)

# Filesystem reads/writes reachable WITHOUT an import — `open` is a builtin and the
# Path methods are attribute calls, so an import denylist alone never sees them.
_IO_CALL_NAMES = frozenset({"open"})
_IO_METHOD_NAMES = frozenset(
    # "open" is here so `builtins.open(...)` — an ast.Attribute, invisible to the
    # bare-name check below — is caught alongside the Path methods.
    {"open", "read_text", "write_text", "read_bytes", "write_bytes", "unlink", "mkdir"}
)


def _io_calls(tree: ast.AST) -> list[str]:
    """Direct filesystem I/O a pure module performs without importing anything."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in _IO_CALL_NAMES:
            found.append(f"{node.func.id}(...)")
        elif isinstance(node.func, ast.Attribute) and node.func.attr in _IO_METHOD_NAMES:
            found.append(f".{node.func.attr}(...)")
    return found


def _attribute_chain(node: ast.AST) -> str:
    """Dotted source spelling of an attribute chain, e.g. `sys.stdout.write`."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _stdout_writes(tree: ast.AST) -> list[str]:
    """Every way this module could write to a stream, not just bare `print(...)`.

    Matching only `ast.Name` missed `builtins.print(...)` and `sys.stdout.write(...)`,
    both of which corrupt `--json` output exactly as much as the bare call does.
    """
    found: list[str] = []
    for node in ast.walk(tree):
        # `from builtins import print` — aliasing it would defeat a call-site check.
        if isinstance(node, ast.ImportFrom) and any(a.name == "print" for a in node.names):
            found.append("imports the print builtin")
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            found.append("print(...)")
        elif isinstance(node.func, ast.Attribute):
            chain = _attribute_chain(node.func)
            if chain.endswith(".print"):
                found.append(f"{chain}(...)")
            elif chain.startswith(("sys.stdout", "sys.stderr")):
                # Prefix, not equality: `sys.stdout.buffer.write(...)` is the standard
                # binary output path and corrupts --json output just as thoroughly.
                found.append(f"{chain}(...)")
    return found


@pytest.mark.parametrize("path", _library_modules(), ids=lambda p: str(p.name))
def test_library_does_not_import_the_command_framework(path: Path) -> None:
    """No typer below `cli/`.

    This is the load-bearing one: it is what makes "the SDK is the same code" true
    rather than aspirational. A library function that raises `typer.Exit` or reads a
    typer context cannot be called from a script.
    """
    parts = _imported_components(ast.parse(path.read_text()))
    for framework in ("typer", "click"):
        assert framework not in parts, f"{path.name} imports {framework}; it belongs under cli/"


@pytest.mark.parametrize("path", _library_modules(), ids=lambda p: str(p.name))
def test_library_does_not_write_to_stdout(path: Path) -> None:
    """No `print()` below `cli/` — progress is reported through callbacks.

    A library that prints is unusable from a notebook and corrupts `--json` output
    when its text lands on stdout alongside the result object.
    """
    writes = _stdout_writes(ast.parse(path.read_text()))
    assert not writes, (
        f"{path.name} writes to a stream ({', '.join(sorted(set(writes)))}); "
        f"emit an event instead — the CLI layer decides where output goes."
    )


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
    hits = sorted(_imported_components(tree) & _FORBIDDEN_IN_PURE)
    assert not hits, (
        f"{path.parent.name}/{path.name} imports {hits}. Pure modules take no I/O layer, "
        f"no network client, and no clock — a decision that reads the clock is not a "
        f"function of its inputs, and its tests stop being a table."
    )
    # Imports alone are not enough: `open(...)` is a builtin and `Path(...).read_text()`
    # is an attribute call, so both reach the filesystem with nothing to deny.
    io = sorted(set(_io_calls(tree)))
    assert not io, (
        f"{path.parent.name}/{path.name} performs filesystem I/O ({', '.join(io)}). "
        f"A decision that depends on local files is not a function of its inputs."
    )


# Spellings generic enough to appear legitimately anywhere — a dict key named "name"
# or "status" is not evidence that response parsing has leaked. Excluded by name so
# the exclusion is reviewable, rather than by quietly omitting them from a hand list.
_AMBIGUOUS_KEYS = frozenset(
    {
        "name",
        "status",
        "key",
        "filename",
        "settings",
        "parameters",
        "required",
        "size",
        "type",
        "batch",
        "jobs",
        # Generic envelope and container words. `http` reads "message" out of an error
        # body — that is transport parsing its own envelope, not a resource's shape —
        # and "path" collides with a dataclass field name that reads no payload.
        "message",
        "error",
        "detail",
        "path",
        "logs",
        "latest",
        "timestamp",
        "published",
        "ref",
    }
)


def _wire_lookup_keys(tree: ast.AST) -> set[str]:
    """Strings a wire module uses to LOOK UP a field: `.get("k")`, `x["k"]`, `*_KEYS`."""
    keys: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("get", "pop")
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            keys.add(node.args[0].value)
        elif (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            keys.add(node.slice.value)
        elif isinstance(node, ast.Assign):
            # Named key collections, e.g. `_NAME_KEYS = ("JobName", "jobName", ...)`.
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.endswith("_KEYS"):
                    for inner in ast.walk(node.value):
                        if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                            keys.add(inner.value)
    return keys


def _shape_spellings() -> frozenset[str]:
    """The response keys `wire` owns — the strings it uses to READ a payload.

    Four versions of this rule have now been wrong. A hand-written list and a list of
    named tuples each RESTATED what the boundary knows and each fell behind it. Reading
    every string constant fixed that but over-reached: it swept in domain VALUES
    ("building", "saved") and field names that merely happen to match a key, so adding
    a resource made the rule fire on code that reads nothing.

    Lookup keys are the precise thing: `.get("k")`, `x["k"]`, and the named `*_KEYS`
    collections. A value a module branches on is not response-shape knowledge; a key it
    reads a payload with, is.
    """
    keys: set[str] = set()
    for path in SRC.rglob("wire.py"):
        keys |= _wire_lookup_keys(ast.parse(path.read_text()))
    return frozenset(keys) - _AMBIGUOUS_KEYS


def test_shape_knowledge_lives_only_at_the_boundary() -> None:
    """The API's key-casing variance is `wire`'s business and nobody else's.

    Before the boundary existed, the same "try JobName, then jobName, then name"
    walk appeared in several places and each copy had to be kept in step. Finding
    those spellings outside `wire` again means a second copy is forming.
    """
    spellings = _shape_spellings()
    offenders = []
    for path in _library_modules():
        # `wire` owns response shapes by definition. `api` is exempt for a different
        # reason: it BUILDS request bodies, so naming the endpoint's own keys
        # ({"jobName": ...}) is its job, not a leak of parsing knowledge. The rule
        # bites on decision and orchestration code, which is where a second copy of
        # the casing rules would actually do damage.
        if path.name in ("wire.py", "api.py"):
            continue
        # AST constants, not a source-text grep: `job.get('JobName')` is the same
        # leak as the double-quoted spelling, and a formatter could rewrite either.
        # Exact equality, so a docstring MENTIONING the key is not a false positive.
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Constant) and node.value in spellings:
                offenders.append(f"{path.parent.name}/{path.name} uses {node.value!r}")
    assert not offenders, "shape knowledge outside wire.py: " + "; ".join(sorted(set(offenders)))


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


def test_every_error_declares_its_own_distinct_exit_code() -> None:
    """Each error condition gets its own code, declared on its own class.

    Two failures this catches, both silent, and neither caught by checking that the
    ExitCode CONSTANTS are unique — that is a different claim:

    1. A new error subclassing a typed one (say `class ToolNotFound(NotFoundError)`)
       without overriding inherits code 4. Nothing fails, and an agent branching on 4
       can no longer tell a missing job from a missing tool.
    2. A new error explicitly reusing another's code — same collapse, spelled out.

    So: the code must be a known ExitCode, declared in the class's OWN body, not the
    generic failure code, and not already taken by a different error.
    """
    from tamarind import errors

    declared = {v for k, v in vars(errors.ExitCode).items() if isinstance(v, int)}
    owner_of: dict[int, str] = {}

    for exc in sorted(_all_error_subclasses(), key=lambda c: c.__name__):
        code = exc.exit_code
        assert code in declared, f"{exc.__name__}.exit_code = {code} is not a value on ExitCode"
        if exc.__name__ in _GENERIC_BY_DESIGN:
            continue
        assert "exit_code" in vars(exc), (
            f"{exc.__name__} inherits its exit code rather than declaring one. Two "
            f"conditions now report the same code and a caller cannot tell them apart."
        )
        assert code != errors.ExitCode.ERROR, (
            f"{exc.__name__} uses the generic ERROR code. Give it its own, or add it "
            f"to _GENERIC_BY_DESIGN with a reason."
        )
        clash = owner_of.get(code)
        assert clash is None, f"{exc.__name__} reuses exit code {code}, already used by {clash}"
        owner_of[code] = exc.__name__


def test_exit_codes_are_distinct() -> None:
    """Two conditions sharing a code makes the code useless for branching."""
    from tamarind import errors

    codes = [v for k, v in vars(errors.ExitCode).items() if isinstance(v, int)]
    assert len(codes) == len(set(codes)), "duplicate ExitCode values"
