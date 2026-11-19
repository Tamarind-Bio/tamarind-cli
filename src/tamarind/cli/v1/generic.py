"""Commands built from the v1 contract.

Every v1 operation names its CLI command in ``x-clients.cli``. Commands written
by hand (today's ``submit``, ``jobs``, ``files upload`` and the rest) take
precedence; every other operation gets a command built here from the manifest:

- path parameters are positional arguments, in path order;
- query parameters are options (``batchId`` → ``--batch-id``; a list takes
  commas or repeats; booleans are ``--x/--no-x``), sent only when given, so the
  server's defaults apply;
- a request body is ``--input FILE`` (YAML or JSON, ``-`` for stdin) plus
  ``--set key=value`` (a YAML value; ``a.b=1`` sets a nested field);
- ``Idempotency-Key`` and ``If-Match`` are ``--idempotency-key`` / ``--if-match``;
- a list operation has ``--all`` to follow ``nextCursor`` to the end.

``--json`` prints the v1 answer as it came; the human form is a table for a
page and key/value lines for an object. Errors keep the CLI's exit codes.
"""

from __future__ import annotations

from typing import Any

import click
from typer.core import TyperGroup

from ...config import API_V1, resolve_api
from ...errors import UsageError, ValidationError
from .. import inputs
from . import manifest, render, sdk

DEFAULT_COMMAND = "_default"
# Hand-written commands that exist only for v1 (no classic counterpart); they stay
# out of --help in classic mode, like the generated ones.
V1_ONLY_COMMANDS = {("files", "download"), ("jobs", "download")}


def option_name(param: dict[str, Any]) -> str:
    return "--" + param["option"]


def _dest(name: str) -> str:
    return sdk.snake(name).replace("-", "_")


def _help(param: dict[str, Any]) -> str:
    text = param.get("description") or ""
    if param.get("enum"):
        text += f" One of: {', '.join(param['enum'])}."
    if "default" in param:
        text += f" Server default: {param['default']}."
    return text.strip()


def query_option(param: dict[str, Any]) -> click.Option:
    dest = "q_" + _dest(param["name"])
    if param["type"] == "boolean":
        flag = param["option"]
        return click.Option(
            [f"--{flag}/--no-{flag}", dest], default=None, help=_help(param), show_default=False
        )
    kind: Any = click.INT if param["type"] == "integer" else click.STRING
    if param["type"] == "array":
        return click.Option(
            [option_name(param), dest],
            multiple=True,
            help=_help(param) + " Comma-separated or repeated.",
        )
    return click.Option(
        [option_name(param), dest], type=kind, required=param.get("required", False), help=_help(param)
    )


def query_values(op: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    """Option values → the operation's query arguments (only those given)."""
    query: dict[str, Any] = {}
    for param in op["query"]:
        value = values.get("q_" + _dest(param["name"]))
        if value is None or value == ():
            continue
        if param["type"] == "array":
            value = [part.strip() for item in value for part in str(item).split(",") if part.strip()]
        query[param["name"]] = value
    return query


def _set_path(body: dict[str, Any], key: str, value: Any) -> None:
    parts = [p for p in key.strip().split(".") if p]
    if not parts:
        raise ValidationError(f"--set needs a field name, got {key!r}.")
    target = body
    for part in parts[:-1]:
        nxt = target.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            target[part] = nxt
        target = nxt
    target[parts[-1]] = value


def load_body(source: str | None, pairs: tuple[str, ...] | list[str]) -> Any:
    """``--input`` document plus ``--set`` overrides; None when neither is given."""
    body: Any = None
    if source:
        body = inputs._parse_document(inputs._load_text(source))
    if pairs:
        if body is None:
            body = {}
        if not isinstance(body, dict):
            raise ValidationError("--set needs --input to be an object.")
        for pair in pairs:
            if "=" not in pair:
                raise ValidationError(f"--set expects key=value, got: {pair!r}")
            key, raw = pair.split("=", 1)
            _set_path(body, key, inputs._coerce_scalar(raw))
    return body


def _command_text(op: dict[str, Any]) -> tuple[str, str]:
    summary = op.get("summary") or op["operationId"]
    text = summary
    if op.get("description") and op["description"] != summary:
        text += "\n\n" + op["description"]
    text += f"\n\nv1 operation: {op['operationId']} ({op['method']} {op['path']})."
    return summary, text


def operation_params(op: dict[str, Any]) -> list[click.Parameter]:
    params: list[click.Parameter] = []
    for param in op["pathParams"]:
        params.append(
            click.Argument([_dest(param["name"])], metavar=sdk.snake(param["name"]).upper())
        )
    params.extend(query_option(q) for q in op["query"])
    if op.get("body") is not None:
        params.append(
            click.Option(
                ["--input", "-i", "input_source"],
                help="Request body as YAML or JSON: a file, '-' for stdin, or @yaml://path.",
            )
        )
        params.append(
            click.Option(
                ["--set", "set_pairs"],
                multiple=True,
                help="Set a body field: key=value (a YAML value; a.b=1 for a nested field). Repeatable.",
            )
        )
    if "Idempotency-Key" in op["headers"]:
        params.append(
            click.Option(
                ["--idempotency-key", "idempotency_key"],
                help="Reuse this key to retry safely across runs (one is generated otherwise).",
            )
        )
    if "If-Match" in op["headers"]:
        params.append(
            click.Option(["--if-match", "if_match"], help="Only act if the ETag still matches.")
        )
    if any(q["name"] == "cursor" for q in op["query"]):
        params.append(
            click.Option(["--all", "all_pages"], is_flag=True, help="Follow nextCursor to the end.")
        )
    return params


def run_operation(op: dict[str, Any], values: dict[str, Any]) -> None:
    ctx = click.get_current_context()
    state = ctx.find_root().obj
    sdk.require_v1(state, op["cli"])
    path_args = [values[_dest(p["name"])] for p in op["pathParams"]]
    query = query_values(op, values)
    body = load_body(values.get("input_source"), values.get("set_pairs") or ())
    if op.get("body") is not None and op["body"].get("required") and body is None:
        # Let the server say which fields are missing, every one at once.
        body = {}
    with sdk.make_client(state) as client:
        if values.get("all_pages"):
            result: Any = sdk.collect(client, op, *path_args, **query)
        else:
            result = sdk.invoke(
                client,
                op,
                *path_args,
                body=body,
                idempotency_key=values.get("idempotency_key"),
                if_match=values.get("if_match"),
                **query,
            )
    render.emit(result, state.output)


def operation_command(op: dict[str, Any], name: str, *, hidden: bool = False) -> click.Command:
    summary, text = _command_text(op)

    def callback(**values: Any) -> None:
        run_operation(op, values)

    command = click.Command(
        name,
        params=operation_params(op),
        callback=callback,
        help=text,
        short_help=summary,
        hidden=hidden,
    )
    command.operation_id = op["operationId"]  # type: ignore[attr-defined]
    return command


def v1_selected(ctx: click.Context) -> bool:
    """Whether this invocation selected v1, for showing v1 commands in --help."""
    state = ctx.find_root().obj
    try:
        is_v1 = getattr(state, "is_v1", None)
    except UsageError:  # a bad `api` setting; the command itself will say so
        return False
    if isinstance(is_v1, bool):
        return is_v1
    import sys

    argv = sys.argv[1:]
    flag = None
    for index, arg in enumerate(argv):
        if arg == "--api" and index + 1 < len(argv):
            flag = argv[index + 1]
        elif arg.startswith("--api="):
            flag = arg.split("=", 1)[1]
    try:
        return resolve_api(flag) == API_V1
    except UsageError:
        return False


class ContractGroup(TyperGroup):
    """A group that also serves the contract's commands under its own path.

    Typer-registered commands win; any other contract command under this path is
    built on first use. In classic mode the v1-only ones stay out of ``--help``
    (they still answer, with a pointer to the v1 setting).
    """

    contract_path: tuple[str, ...] | None = None
    default_operation: str | None = None
    # Names listed first, in this order (keeps today's --help order where Typer
    # would put groups after commands).
    command_order: tuple[str, ...] = ()

    def path(self, ctx: click.Context) -> tuple[str, ...]:
        if self.contract_path is not None:
            return self.contract_path
        names: list[str] = []
        current: click.Context | None = ctx
        while current is not None and current.parent is not None:
            names.append(current.info_name or "")
            current = current.parent
        return tuple(reversed(names))

    def list_commands(self, ctx: click.Context) -> list[str]:
        names = [n for n in super().list_commands(ctx) if n != DEFAULT_COMMAND]
        path = self.path(ctx)
        if v1_selected(ctx):
            for name in manifest.children(path):
                if name not in names:
                    names.append(name)
        else:
            names = [n for n in names if path + (n,) not in V1_ONLY_COMMANDS]
        if self.command_order:
            rank = {name: i for i, name in enumerate(self.command_order)}
            names.sort(key=lambda n: rank.get(n, len(rank)))
        return names

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        command = super().get_command(ctx, cmd_name)
        if command is not None:
            return command
        path = self.path(ctx)
        if cmd_name == DEFAULT_COMMAND and self.default_operation:
            return operation_command(manifest.operation(self.default_operation), DEFAULT_COMMAND, hidden=True)
        return build(path + (cmd_name,))

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if self.default_operation and not any(a in ("--help", "-h") for a in args[:1]):
            known = set(self.list_commands(ctx)) | set(manifest.children(self.path(ctx)))
            if not args or args[0] not in known:
                args = [DEFAULT_COMMAND, *args]
        return super().parse_args(ctx, args)


def group_for(path: tuple[str, ...]) -> ContractGroup:
    op = manifest.by_cli_path().get(path)
    help_text = manifest.group_help(path)
    group = ContractGroup(
        name=path[-1], no_args_is_help=op is None, help=help_text, short_help=help_text
    )
    group.contract_path = path
    if op is not None:
        group.default_operation = op["operationId"]
        summary, text = _command_text(op)
        group.help = text + "\n\nWith no subcommand, runs this operation."
        group.short_help = summary
    return group


def build(path: tuple[str, ...]) -> click.Command | None:
    """The command (or group) for a contract path, or None if the contract has none."""
    if manifest.has_children(path):
        return group_for(path)
    op = manifest.by_cli_path().get(path)
    if op is None:
        return None
    return operation_command(op, path[-1])


class RootGroup(ContractGroup):
    """The ``tamarind`` group: today's command order, then the v1 groups."""

    command_order = (
        "tools",
        "modalities",
        "functions",
        "schema",
        "validate",
        "submit",
        "batch",
        "jobs",
        "status",
        "wait",
        "results",
        "logs",
        "cancel",
        "delete",
        "auth",
        "custom-tools",
        "files",
    )
