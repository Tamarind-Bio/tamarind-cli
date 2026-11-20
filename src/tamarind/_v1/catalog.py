"""Today's catalog requests, answered by v1's tool routes.

``tamarind.catalog`` (and ``Tamarind().tools``, and the CLI's ``tools``, ``modalities``,
``functions`` and ``schema``) read four catalog routes. With v1 on for the key they are
answered from v1 and rebuilt in the catalog's layout:

- ``catalog/tools`` from every page of ``listTools``, filtered, sorted and summarized the
  way the catalog does it (``getAvailableTools`` in the MCP server), so its filters,
  facet lists and hints behave as before. ``custom=true`` stays on the catalog: v1 lists
  built-in tools only.
- ``catalog/modalities`` and ``catalog/functions`` from ``getToolFacets``.
- ``catalog/tools/{tool}/schema`` from ``getToolSchema`` (and ``getTool`` for the
  display name and facets). v1's JSON Schema is rebuilt as the catalog's parameter
  list, as far as v1 carries it: each setting's name, type, display name, description,
  default, required, options, bounds and example. The catalog's other setting keys
  (``constraints``, ``constraintsText``, ``conditionals``, ``tasks``...) have no v1
  form; v1 folds the constraints into the description and the conditions into
  ``allOf``. ``exampleJob`` is v1's ``example``, built for one task branch.

The tool list is v1's, so it is the app's list (website#7796): tools the app doesn't
list for the caller aren't listed, and facet counts follow. docs/v1-mode.md has the
differences.
"""

from __future__ import annotations

from typing import Any

from ..errors import NotFoundError, TamarindError
from .classic import OnClassic, Router, plain
from .errors import ProblemError

PAGE = 200
# What the catalog cuts a narrowed listing's descriptions to (`_simplify_tool`).
DESCRIPTION_CHARS = 150
# A bound v1 sends for a number the catalog leaves unbounded.
_NO_BOUND = 999_999_999_999_999
# The catalog's file setting types (`_FILE_SETTING_TYPES`), which change the example's note.
FILE_TYPES = frozenset(
    {"pdb", "sdf", "mol2", "mol", "cif", "fasta", "file", "structure", "molecules", "binary", "smiles", "image"}
)

LIST_HINT = (
    "Use getJobSchema(jobType='<name>') for a tool's description + parameters. Pass the exact `name` "
    "(lowercase, e.g. 'alphafold'), not the displayName. Filter with category=/tag= using the values "
    "in availableCategories/availableTags."
)
FULL_LIST_HINT = (
    " Descriptions are omitted in this full listing — filter with modality=/function=/search= to get "
    "them (see listModalities()/listTags()), or getJobSchema a specific tool."
)
MODALITIES_HINT = (
    "Filter the catalog with getAvailableTools(modality='<value>'). Combine with function= (see "
    "listTags()) to narrow further."
)
FUNCTIONS_HINT = (
    "Filter the catalog with getAvailableTools(function='<value>'). Combine with modality= (see "
    "listModalities()) to narrow further."
)
SCHEMA_HINT = (
    "For file parameters, you can use s3Path values from listJobFiles() to chain jobs without "
    "downloading/uploading"
)
NOT_FOUND_HINT = "Use getAvailableTools() or getAvailableTools(custom=true) to see all available tools"
# What the catalog adds to `outputs` when a tool's outputs depend on its task (`_tool_outputs`).
BY_TASK_NOTE = (
    "This tool's output depends on the task it runs. `byTask` is authoritative for the task you set, and "
    "each entry is COMPLETE — a task that does not redeclare `mainCSV`/`taskType` inherits the tool's "
    "top-level value. The `taskType`, `mainCSV` and `produces` above summarize ACROSS tasks: `produces` is "
    "the union over every task's output — as a column OR as a file written alongside the CSV — and "
    "`taskType`/`mainCSV` are the tool's top-level declaration, which is not guaranteed to be the task "
    "selector's default. Do not read them as describing the run you are about to submit. `generates` is "
    "what a task creates fresh (empty for a scoring task, whose table may still echo its input). A column "
    "carrying a `tasks` list appears only in those tasks; an untagged column is simply not task-gated in "
    "the tool's declaration, which does not promise every task fills it — read `generates` for what a task "
    "actually produces. An ABSENT `generates` means the tool declared none for that task, not that the task "
    "generates nothing."
)


def missing(exc: BaseException) -> bool:
    """A v1 404 (inside a handler it is still v1's ``ProblemError``)."""
    return isinstance(exc, NotFoundError) or (isinstance(exc, ProblemError) and exc.status == 404)


def _example_note(has_file: bool) -> str:
    """The catalog's ``exampleJobNote`` (``_example_job_note``)."""
    note = "Illustrative example built from each parameter's example/default. "
    if has_file:
        note += (
            "Some inputs are files (e.g. .pdb/.sdf) — upload them first with uploadFile, or pass an "
            "s3Path from listJobFiles(); the sample filenames here are placeholders. "
        )
    else:
        note += "Inputs are sequence/text, so this is directly runnable via submitJob. "
    return note + "Use validateJob to check settings before submitting."


# -- catalog/tools ----------------------------------------------------------------------


def _every_tool(client: Router) -> list[dict[str, Any]]:
    v1 = client.v1()
    return [plain(tool) for tool in v1.paginate(v1.tools.list, limit=PAGE)]


def _summary(tool: dict[str, Any], *, full: bool) -> dict[str, Any]:
    """A listing's tool, as the catalog's ``_simplify_tool`` writes it."""
    out: dict[str, Any] = {
        "name": tool.get("name"),
        "displayName": tool.get("displayName") or tool.get("name"),
        "categories": list(tool.get("modalities") or []),
    }
    if tool.get("outputTypes"):
        out["outputTypes"] = list(tool["outputTypes"])
    if full:
        out["tags"] = list(tool.get("functions") or [])
        out["description"] = str(tool.get("description") or "")[:DESCRIPTION_CHARS]
    return out


def list_tools(client: Router, params: dict[str, Any]) -> dict[str, Any]:
    """GET catalog/tools → every page of listTools, narrowed as the catalog narrows: a
    modality or function matched in any case, ``search`` in the name, display name or
    description, sorted by name. The facet lists, and which filter values are
    unrecognized, come from the whole list, before narrowing."""
    if str(params.get("custom")).lower() == "true":
        raise OnClassic  # v1's listTools holds built-in tools only (custom=true is 400)
    modality = params.get("modality") or params.get("category") or None
    function = params.get("function") or params.get("tag") or None
    search = params.get("search") or None
    tools = _every_tool(client)

    modalities = {str(m) for tool in tools for m in tool.get("modalities") or []}
    functions = {str(f) for tool in tools for f in tool.get("functions") or []}
    unrecognized: dict[str, str] = {}
    if modality and modality.lower() not in {m.lower() for m in modalities}:
        unrecognized["modality"] = modality
    if function and function.lower() not in {f.lower() for f in functions}:
        unrecognized["function"] = function

    if modality:
        tools = [t for t in tools if modality.lower() in [str(m).lower() for m in t.get("modalities") or []]]
    if function:
        tools = [t for t in tools if function.lower() in [str(f).lower() for f in t.get("functions") or []]]
    if search:
        needle = search.lower()
        tools = [
            t for t in tools
            if any(needle in str(t.get(key) or "").lower() for key in ("name", "displayName", "description"))
        ]
    tools.sort(key=lambda t: str(t.get("name") or ""))

    narrowed = bool(search or modality or function)
    hint = LIST_HINT + ("" if narrowed else FULL_LIST_HINT)
    if unrecognized:
        hint += (
            f" NOTE: unrecognized filter value(s) {unrecognized} — these are not valid; call "
            "listModalities()/listTags() for valid values."
        )
    summaries = [_summary(t, full=narrowed) for t in tools]
    out: dict[str, Any] = {
        "totalTools": len(summaries),
        "filters": {"modality": modality, "function": function, "search": search},
        "descriptionsOmitted": not narrowed,
        "availableCategories": sorted(modalities),
        "availableTags": sorted(functions),
        "tools": summaries,
        "hint": hint,
    }
    if unrecognized:
        out["unrecognizedFilters"] = unrecognized
    return out


# -- catalog/modalities, catalog/functions ------------------------------------------------


def _facet_listing(client: Router, axis: str) -> list[dict[str, Any]]:
    """One axis of getToolFacets as the catalog lists it: ``{value, label, toolCount,
    description?}``, most tools first, then by value."""
    facets = plain(client.v1().tools.facets()) or {}
    entries = []
    for facet in facets.get(axis) or []:
        value = facet.get("name")
        entry: dict[str, Any] = {
            "value": value,
            "label": facet.get("label") or value,
            "toolCount": int(facet.get("toolCount") or 0),
        }
        if facet.get("description"):
            entry["description"] = facet["description"]
        entries.append(entry)
    entries.sort(key=lambda e: (-e["toolCount"], str(e["value"])))
    return entries


def list_modalities(client: Router, params: dict[str, Any]) -> dict[str, Any]:
    """GET catalog/modalities → getToolFacets' modalities."""
    entries = _facet_listing(client, "modalities")
    return {
        "modalities": entries,
        "descriptionsAvailable": any("description" in e for e in entries),
        "hint": MODALITIES_HINT,
    }


def list_functions(client: Router, params: dict[str, Any]) -> dict[str, Any]:
    """GET catalog/functions → getToolFacets' functions."""
    entries = _facet_listing(client, "functions")
    return {
        "functions": entries,
        "descriptionsAvailable": any("description" in e for e in entries),
        "hint": FUNCTIONS_HINT,
    }


# -- catalog/tools/{tool}/schema ----------------------------------------------------------


def _classic_type(prop: dict[str, Any]) -> Any:
    """A setting's catalog type: v1's ``x-tamarind-type``, else its JSON type (a number,
    integer or boolean v1 also takes as text is that type; an integer is the catalog's
    ``number``; a list is its items' type)."""
    if prop.get("x-tamarind-type"):
        return prop["x-tamarind-type"]
    kind = prop.get("type")
    if isinstance(kind, list):
        kind = next((k for k in kind if k not in ("string", "null")), "string")
    if kind == "array":
        items = prop.get("items")
        return _classic_type(items) if isinstance(items, dict) else kind
    return "number" if kind == "integer" else kind


def _bound(value: Any) -> Any:
    if isinstance(value, (int, float)) and abs(value) >= _NO_BOUND:
        return None
    return value


def _parameter(name: str, prop: dict[str, Any], required: set[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"name": name, "type": _classic_type(prop)}
    if prop.get("title"):
        out["displayName"] = prop["title"]
    if prop.get("description"):
        out["descr"] = prop["description"]
    if "default" in prop:
        out["default"] = prop["default"]
    if name in required:
        out["required"] = True
    if isinstance(prop.get("enum"), list):
        out["options"] = list(prop["enum"])
    for key, v1_key in (("lowerBound", "minimum"), ("upperBound", "maximum")):
        bound = _bound(prop.get(v1_key))
        if bound is not None:
            out[key] = bound
    examples = prop.get("examples")
    if not examples and isinstance(prop.get("items"), dict):
        examples = prop["items"].get("examples")
    if isinstance(examples, list) and examples:
        out["example"] = examples[0]
    return out


def _required(schema: dict[str, Any]) -> set[str]:
    """The settings the catalog marks required: v1's ``required``, and those its ``allOf``
    rules require on some branch (``if`` a task or a switch, ``then`` required), which the
    catalog flags required too. A required setting with a default isn't required on v1,
    since v1 fills it in, so it isn't flagged."""
    names = {str(name) for name in schema.get("required") or []}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            then = node.get("then")
            if isinstance(then, dict):
                names.update(str(name) for name in then.get("required") or [])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema.get("allOf") or [])
    return names


def _without_nulls(value: Any) -> Any:
    """The catalog leaves out what v1 sends as null."""
    if isinstance(value, dict):
        return {k: _without_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_without_nulls(v) for v in value]
    return value


def tool_schema(client: Router, tool: str, params: dict[str, Any]) -> dict[str, Any]:
    """GET catalog/tools/{tool}/schema → getToolSchema (+ getTool), in the catalog's
    layout. A tool v1 doesn't serve gets the catalog's 200 ``{error, hint}``."""
    v1 = client.v1()
    try:
        answer = plain(v1.tools.schema(tool))
    except TamarindError as exc:
        if not missing(exc):
            raise
        return {"error": f"Tool '{tool}' not found in standard or custom tools", "hint": NOT_FOUND_HINT}
    schema = answer.get("schema") or {}
    try:
        facts = plain(v1.tools.get(tool))
    except TamarindError as exc:
        if not missing(exc):
            raise
        facts = {}  # a custom tool: getTool serves built-in tools only
    required = _required(schema)
    properties = schema.get("properties") or {}
    parameters = [
        _parameter(str(name), prop, required) for name, prop in properties.items() if isinstance(prop, dict)
    ]
    out: dict[str, Any] = {
        "jobType": tool,
        "displayName": facts.get("displayName") or tool,
        "description": facts.get("description") or schema.get("description") or "",
        "parameters": parameters,
        "categories": list(facts.get("modalities") or []),
        "tags": list(facts.get("functions") or []),
        "hint": SCHEMA_HINT,
    }
    if answer.get("outputTypes"):
        out["outputTypes"] = list(answer["outputTypes"])
    if answer.get("outputContract"):
        outputs = _without_nulls(answer["outputContract"])
        if outputs.get("byTask"):
            outputs["byTaskNote"] = BY_TASK_NOTE
        out["outputs"] = outputs
    example = answer.get("example")
    if isinstance(example, dict) and example:
        types = {p["name"]: str(p.get("type") or "").lower() for p in parameters}
        out["exampleJob"] = {"jobName": f"{tool}-example", "type": tool, "settings": dict(example)}
        out["exampleJobNote"] = _example_note(any(types.get(name) in FILE_TYPES for name in example))
    return out
