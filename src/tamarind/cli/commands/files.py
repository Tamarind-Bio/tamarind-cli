"""`tamarind files` — workspace file management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import httpx
import typer

from ... import rest
from ...errors import TamarindError
from .. import output

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_files(
    ctx: typer.Context,
    types: Optional[str] = typer.Option(None, "--types", help="Comma-separated extensions, e.g. 'pdb,cif'."),
    search: Optional[str] = typer.Option(None, "--search", "-s", help="Filter filenames by substring."),
    folder: Optional[str] = typer.Option(None, "--folder", help="List within this folder."),
    limit: int = typer.Option(50, "--limit", help="Max files to return."),
    offset: int = typer.Option(0, "--offset", help="Pagination offset."),
    metadata: bool = typer.Option(False, "--metadata", help="Include size/lastModified."),
    all_dirs: bool = typer.Option(False, "--all", help="Recurse into subdirectories."),
) -> None:
    """List files in your workspace."""
    state = ctx.obj
    with state.rest_client() as client:
        resp = rest.get_files(
            client,
            limit=limit,
            offset=offset,
            types=types,
            search=search,
            folder=folder,
            include_all=all_dirs,
            include_metadata=metadata,
        )
    files = resp.get("files", []) if isinstance(resp, dict) else resp
    if files and isinstance(files[0], dict):
        rows = [{"name": f.get("name"), "size": f.get("size"), "lastModified": f.get("lastModified")} for f in files]
        human = output.render_table(rows, ["name", "size", "lastModified"])
    else:
        human = "\n".join(str(f) for f in files) or "(none)"
    output.emit(resp, state.output, human=human)


@app.command()
def folders(
    ctx: typer.Context,
    limit: int = typer.Option(50, "--limit", help="Max folders to return."),
    all_folders: bool = typer.Option(False, "--all", help="Load all folders."),
) -> None:
    """List folders in your workspace."""
    state = ctx.obj
    with state.rest_client() as client:
        resp = rest.get_folders(client, limit=limit, load_all=all_folders)
    folder_list = resp.get("folders", []) if isinstance(resp, dict) else resp
    output.emit(resp, state.output, human="\n".join(str(f) for f in folder_list) or "(none)")


@app.command()
def upload(
    ctx: typer.Context,
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="Local file to upload."),
    name: Optional[str] = typer.Option(None, "--name", help="Remote filename (default: the local basename)."),
) -> None:
    """Upload a local file to your workspace (two-step presigned PUT)."""
    state = ctx.obj
    remote = name or path.name
    with state.rest_client() as client:
        signed = rest.upload_file_url(client, filename=remote)
    url = signed.get("signedUrl")
    if not url:
        raise TamarindError("Upload did not return a signed URL.", detail=signed)
    output.info(f"Uploading {path} → {remote}…", state.output)
    with path.open("rb") as fh:
        put = httpx.put(url, content=fh.read(), timeout=300.0)
    put.raise_for_status()
    output.emit(
        {"ok": True, "filename": remote, "bytes": path.stat().st_size},
        state.output,
        human=f"uploaded {remote}",
    )


@app.command()
def delete(
    ctx: typer.Context,
    path: Optional[str] = typer.Argument(None, help="File path to delete."),
    folder: Optional[str] = typer.Option(None, "--folder", help="Delete every file under this folder instead."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete a file, or every file under a folder."""
    state = ctx.obj
    if not path and not folder:
        raise TamarindError("Provide a file path or --folder <name>.")
    target = path or f"folder {folder}"
    if not yes and not state.output.json:
        typer.confirm(f"Delete {target}?", abort=True)
    with state.rest_client() as client:
        resp = rest.delete_file(client, file_path=path, folder=folder)
    human = resp.get("message", resp) if isinstance(resp, dict) else resp
    output.emit(resp, state.output, human=str(human))
