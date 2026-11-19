"""Parity with the v1 contract: every operation has a CLI command.

The contract (``openapi/api-v1.yaml``) names each operation's command in
``x-clients.cli`` (DESIGN "Parity": SDK and CLI cover all of them). These tests
fail when the CLI's manifest is stale, or when an operation names a command the
CLI doesn't have.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import click
import pytest
import typer
import yaml

from tamarind.cli.main import app
from tamarind.cli.v1 import manifest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "openapi" / "api-v1.yaml"


def _generator():
    spec = importlib.util.spec_from_file_location("gen_v1_cli_manifest", ROOT / "scripts" / "gen_v1_cli_manifest.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _contract_operations():
    doc = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    for path, item in doc["paths"].items():
        for method, op in item.items():
            if method in ("get", "post", "put", "patch", "delete"):
                yield path, method, op


def test_manifest_matches_the_vendored_contract():
    gen = _generator()
    expected = gen.render(gen.build(yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))))
    current = (ROOT / "src" / "tamarind" / "cli" / "v1" / "_operations.json").read_text(encoding="utf-8")
    assert current == expected, "run: uv run python scripts/gen_v1_cli_manifest.py"


def test_every_contract_operation_names_a_cli_command_and_sdk_method():
    missing = [
        op.get("operationId")
        for _, _, op in _contract_operations()
        if not (op.get("x-clients") or {}).get("cli") or not (op.get("x-clients") or {}).get("sdk")
    ]
    assert missing == []


@pytest.fixture(autouse=True)
def _v1_selected(monkeypatch, tmp_path):
    """The contract's commands are the CLI's with v1 selected."""
    monkeypatch.setenv("TAMARIND_API", "v1")
    monkeypatch.setenv("TAMARIND_CONFIG_DIR", str(tmp_path))


def _resolve(path: tuple[str, ...]) -> tuple[click.Command, click.Context]:
    """The command ``tamarind <path>`` runs, found the way click dispatches it."""
    root = typer.main.get_command(app)
    ctx = click.Context(root, info_name="tamarind")
    command: click.Command = root
    args = list(path)
    while args:
        assert isinstance(command, click.Group), f"{' '.join(path)}: {command.name} is not a group"
        name, found, args = command.resolve_command(ctx, args)
        assert found is not None, f"no command `tamarind {' '.join(path)}` (stops at {name!r})"
        ctx = click.Context(found, info_name=name, parent=ctx)
        command = found
    return command, ctx


@pytest.mark.parametrize(
    "operation_id,cli",
    [(op["operationId"], op["cli"]) for op in manifest.operations()],
)
def test_every_operation_has_its_cli_command(operation_id, cli):
    command, _ = _resolve(tuple(cli.split()))
    if isinstance(command, click.Group) and not getattr(command, "invoke_without_command", False):
        # A path that is both a command and a group runs its operation by default.
        assert getattr(command, "default_operation", None) == operation_id, cli


def test_generated_commands_take_path_params_as_arguments_and_query_as_options():
    command, _ = _resolve(("projects", "members"))
    names = [p.name for p in command.params]
    assert names[0] == "project_id"
    assert "q_limit" in names and "q_cursor" in names and "all_pages" in names
    command, _ = _resolve(("molecules", "create-group"))
    opts = {o for p in command.params for o in getattr(p, "opts", [])}
    assert {"--input", "--set"} <= opts


def _generated_endpoint(operation_id: str):
    import importlib
    import pkgutil

    import tamarind.v1._generated.api as api

    name = sdk_snake(operation_id)
    for package in pkgutil.iter_modules(api.__path__):
        try:
            return importlib.import_module(f"{api.__name__}.{package.name}.{name}")
        except ModuleNotFoundError:
            continue
    raise AssertionError(f"no generated module for {operation_id}")


def sdk_snake(name: str) -> str:
    from tamarind.cli.v1.sdk import snake

    return snake(name)


@pytest.mark.parametrize("op", list(manifest.operations()), ids=lambda op: op["operationId"])
def test_cli_argument_names_match_the_generated_sdk(op):
    """The CLI passes each query parameter under the keyword the SDK's generated
    request builder takes (``createdBy`` → ``created_by``, ``from`` → ``from_``)."""
    import inspect

    from tamarind.cli.v1.sdk import argument

    accepted = set(inspect.signature(_generated_endpoint(op["operationId"])._get_kwargs).parameters)
    wanted = {argument(p["name"]) for p in op["query"]} | {argument(p["name"]) for p in op["pathParams"]}
    assert wanted <= accepted, sorted(wanted - accepted)


def test_groups_that_need_a_subcommand_say_so_in_json_mode():
    from tamarind.cli import main

    needs_subcommand = {
        name
        for name in manifest.children(())
        if manifest.has_children((name,)) and (name,) not in manifest.by_cli_path()
    } - {"jobs", "tools"}
    assert needs_subcommand <= main._COMMAND_GROUPS
