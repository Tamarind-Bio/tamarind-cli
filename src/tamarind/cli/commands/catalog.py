"""Discovery commands: `tamarind tools|modalities|functions|schema`."""

from __future__ import annotations

import re
from typing import Optional

import typer

from ... import catalog
from .. import output


def _rewrite_mcp_operations(text: object) -> object:
    """Translate known MCP-operation boilerplate while preserving other guidance."""
    if not isinstance(text, str):
        return text
    replacements = (
        (r"\bgetJobSchema\s*\([^)]*\)", "`tamarind --json schema NAME`"),
        (r"\blistJobFiles\s*\([^)]*\)", "the downloaded result bundle"),
        (r"\bvalidateJob\b", "`tamarind --json validate`"),
        (r"\bsubmitJob\b", "`tamarind --json submit`"),
    )
    rewritten = text
    for pattern, replacement in replacements:
        rewritten = re.sub(pattern, replacement, rewritten)
    return rewritten


def _with_cli_tools_hint(response: object) -> object:
    """Preserve catalog guidance and add instructions valid in this CLI."""
    if not isinstance(response, dict):
        return response
    result = dict(response)
    if "hint" in result:
        result["hint"] = _rewrite_mcp_operations(result["hint"])
    result["cliHint"] = (
        "Inspect a tool with `tamarind --json schema NAME`. Pass the exact lowercase "
        "tool name, and narrow discovery with `--modality` or `--function`."
    )
    return result


def _with_cli_schema_hints(response: object, tool: str) -> object:
    """Keep live schema data while preventing MCP-only instructions from leaking in."""
    if not isinstance(response, dict) or response.get("error"):
        return response
    result = dict(response)
    if "hint" in result:
        result["hint"] = _rewrite_mcp_operations(result["hint"])
    result["cliHint"] = (
        f"Validate settings with `tamarind --json validate {tool} --input FILE`. "
        "Upload local file inputs with `tamarind --json files upload PATH`; download "
        "completed outputs with `tamarind --json results JOB --download DIR`."
    )
    if "exampleJobNote" in result:
        result["exampleJobNote"] = _rewrite_mcp_operations(result["exampleJobNote"])
    return result


def register(app: typer.Typer) -> None:
    @app.command()
    def tools(
        ctx: typer.Context,
        modality: Optional[str] = typer.Option(None, "--modality", "-m", help="Filter by molecule type (see `tamarind modalities`)."),
        function: Optional[str] = typer.Option(None, "--function", "-f", help="Filter by function/tag (see `tamarind functions`)."),
        search: Optional[str] = typer.Option(None, "--search", "-s", help="Free-text search in name/description."),
        custom: bool = typer.Option(False, "--custom", help="Show only your org's custom tools."),
    ) -> None:
        """List available tools. Filter to narrow the (large) catalog."""
        state = ctx.obj
        with state.catalog_client() as client:
            resp = catalog.list_tools(
                client, modality=modality, function=function, search=search, custom=custom or None
            )
        resp = _with_cli_tools_hint(resp)
        rows = [
            {
                "name": t.get("name"),
                "displayName": t.get("displayName"),
                "modalities": ",".join(t.get("categories", []) or []),
            }
            for t in resp.get("tools", [])
        ]
        human = (
            output.render_table(rows, ["name", "displayName", "modalities"])
            + f"\n\n{resp.get('totalTools', len(rows))} tools. "
            "Use `tamarind schema <name>` for parameters."
        )
        output.emit(resp, state.output, human=human)

    @app.command()
    def modalities(ctx: typer.Context) -> None:
        """List molecule types (modalities) you can filter tools by."""
        state = ctx.obj
        with state.catalog_client() as client:
            resp = catalog.list_modalities(client)
        rows = [
            {"value": m.get("value"), "label": m.get("label"), "tools": m.get("toolCount")}
            for m in resp.get("modalities", [])
        ]
        output.emit(resp, state.output, human=output.render_table(rows, ["value", "label", "tools"]))

    @app.command()
    def functions(ctx: typer.Context) -> None:
        """List functions (tags) you can filter tools by."""
        state = ctx.obj
        with state.catalog_client() as client:
            resp = catalog.list_functions(client)
        rows = [
            {"value": f.get("value"), "label": f.get("label"), "tools": f.get("toolCount")}
            for f in resp.get("functions", [])
        ]
        output.emit(resp, state.output, human=output.render_table(rows, ["value", "label", "tools"]))

    @app.command()
    def schema(
        ctx: typer.Context,
        tool: str = typer.Argument(..., help="Tool name (lowercase, e.g. 'boltz')."),
        example: bool = typer.Option(False, "--example", help="Print only the runnable example settings (YAML). Not every tool ships an example."),
    ) -> None:
        """Show a tool's parameters and a runnable example job."""
        state = ctx.obj
        with state.catalog_client() as client:
            resp = catalog.get_schema(client, tool)
        resp = _with_cli_schema_hints(resp, tool)
        # The catalog returns HTTP 200 with {"error": ...} for an unknown/hidden
        # tool; turn that into a not-found exit instead of printing it as success.
        if isinstance(resp, dict) and resp.get("error"):
            from ...errors import NotFoundError

            raise NotFoundError(resp["error"])

        if example:
            import yaml

            settings = catalog.example_settings(resp)
            # Not every tool ships an example. Fail loudly instead of printing an
            # empty `{}` at exit 0 — otherwise `tamarind schema <tool> --example
            # > job.yaml` silently writes an empty file that looks like success.
            if not settings:
                from ...errors import NotFoundError

                raise NotFoundError(
                    f"No runnable example is available for '{tool}'. "
                    f"Run `tamarind schema {tool}` to see its parameters and "
                    "build the settings by hand."
                )
            output.emit(
                {"type": tool, "settings": settings},
                state.output,
                human=yaml.safe_dump(settings, sort_keys=False).rstrip(),
            )
            return

        param_rows = []
        for p in resp.get("parameters", []):
            param_rows.append(
                {
                    "name": p.get("name"),
                    "type": p.get("type"),
                    "required": "yes" if p.get("required") else "",
                    "default": p.get("default"),
                    # Full text — render_table truncates it (with an ellipsis) to fit.
                    "description": p.get("descr") or p.get("description") or p.get("displayName") or "",
                }
            )
        human = (
            f"{resp.get('displayName', tool)}  [{tool}]\n"
            f"{resp.get('description', '')}\n\n"
            + output.render_table(param_rows, ["name", "type", "required", "default", "description"])
            + "\n\nRun `tamarind schema "
            + tool
            + " --example` for runnable example settings."
        )
        output.emit(resp, state.output, human=human)
