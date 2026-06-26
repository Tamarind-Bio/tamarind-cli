"""Discovery commands: `tamarind tools|modalities|functions|schema`."""

from __future__ import annotations

from typing import Optional

import typer

from ... import catalog
from .. import output


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
        example: bool = typer.Option(False, "--example", help="Print only the runnable example settings (YAML)."),
    ) -> None:
        """Show a tool's parameters and a runnable example job."""
        state = ctx.obj
        with state.catalog_client() as client:
            resp = catalog.get_schema(client, tool)

        if example:
            import yaml

            settings = catalog.example_settings(resp)
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
                    "description": (p.get("descr") or p.get("displayName") or "")[:60],
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
