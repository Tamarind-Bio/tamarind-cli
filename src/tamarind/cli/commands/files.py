"""`tamarind files` — workspace file management."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ... import rest, uploads
from ...errors import TamarindError
from ...file_pages import collect_file_pages
from .. import output

app = typer.Typer(no_args_is_help=True)


def _file_name(f: object) -> str:
    """A file entry is usually a bare name string, but be tolerant of dicts."""
    if isinstance(f, str):
        return f
    if isinstance(f, dict):
        return str(f.get("name") or f.get("filename") or f.get("key") or "")
    return str(f)


def _apply_file_filters(
    files: list,
    *,
    types: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> dict:
    """Filter a workspace file list client-side, mirroring the MCP ``getFiles`` tool.

    The ``/files`` REST endpoint returns the full, unfiltered list and ignores the
    ``types``/``search``/``limit``/``offset`` query params, so the CLI applies them
    here — using the same rules as ``getFiles`` (main.py) — to keep the two surfaces
    in parity. Returns the same envelope shape the MCP tool returns.
    """
    total_unfiltered = len(files)
    if types:
        exts = [t.strip().lower().lstrip(".") for t in types.split(",") if t.strip()]
        files = [f for f in files if any(_file_name(f).lower().endswith(f".{e}") for e in exts)]
    if search:
        needle = search.lower()
        files = [f for f in files if needle in _file_name(f).lower()]
    filtered_count = len(files)
    start = max(offset or 0, 0)
    page = files[start : start + limit] if limit is not None else files[start:]
    has_more = (start + limit) < filtered_count if limit is not None else False
    return {
        "files": page,
        "count": len(page),
        "total": filtered_count,
        "totalUnfiltered": total_unfiltered,
        "hasMore": has_more,
        "offset": start,
        "limit": limit,
        "filters": {"types": types, "search": search},
    }


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
    # Collect bounded catalog pages before applying the established CLI filters.
    # --all retains the legacy API path; version 2 is a directory listing.
    with state.rest_client() as client:
        resp = (rest.get_files(client, folder=folder, include_all=True, include_metadata=metadata)
                if all_dirs else collect_file_pages(client, folder=folder, include_metadata=metadata))
    files = resp.get("files") if isinstance(resp, dict) else resp
    if not isinstance(files, list):
        files = []
    result = _apply_file_filters(files, types=types, search=search, limit=limit, offset=offset)
    page = result["files"]
    if page and isinstance(page[0], dict):
        rows = [{"name": _file_name(f), "size": f.get("size"), "lastModified": f.get("lastModified")} for f in page]
        human = output.render_table(rows, ["name", "size", "lastModified"])
    else:
        human = "\n".join(_file_name(f) for f in page) or "(none)"
    if result["hasMore"]:
        human += f"\n\n{result['count']} of {result['total']} shown — use --offset {result['offset'] + limit} for the next page."
    output.emit(result, state.output, human=human)


def _file_type_counts(files: list) -> dict:
    """Count workspace files by extension, mirroring the MCP getFileStats tool."""
    counts: dict = {}
    for f in files:
        name = _file_name(f)
        ext = name.rsplit(".", 1)[1].lower() if "." in name else "no_extension"
        counts[ext] = counts.get(ext, 0) + 1
    # Sort by count desc (then name for stable ties); keep the top 20 like getFileStats.
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
    return dict(ordered)


@app.command()
def stats(ctx: typer.Context) -> None:
    """Summarize workspace files by type (counts), like the MCP getFileStats tool."""
    state = ctx.obj
    with state.rest_client() as client:
        resp = collect_file_pages(client)
    files = resp.get("files") if isinstance(resp, dict) else resp
    if not isinstance(files, list):
        files = []
    file_types = _file_type_counts(files)
    out = {
        "totalFiles": len(files),
        "fileTypes": file_types,
        "hint": "Use `tamarind files list --types pdb` to list a specific type.",
    }
    rows = [{"type": k, "count": v} for k, v in file_types.items()]
    human = output.render_table(rows, ["type", "count"]) + f"\n\n{len(files)} files total."
    output.emit(out, state.output, human=human)


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
    folder_list = resp.get("folders") if isinstance(resp, dict) else resp
    if not isinstance(folder_list, list):
        folder_list = []
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
    output.info(f"Uploading {path} → {remote}…", state.output)
    with state.rest_client() as client:
        # Shared with the SDK's `client.files.upload` — one presign-then-PUT code path.
        result = uploads.upload_file(client, path, remote=remote)
    output.emit(result, state.output, human=f"uploaded {result['filename']}")


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
    output.confirm_destructive(f"delete {target}", yes=yes, mode=state.output)
    with state.rest_client() as client:
        resp = rest.delete_file(client, file_path=path, folder=folder)
    human = resp.get("message", resp) if isinstance(resp, dict) else resp
    output.emit(resp, state.output, human=str(human))
