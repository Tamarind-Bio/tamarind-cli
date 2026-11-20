"""The catalog (``tamarind.catalog``, ``Tamarind().tools``, the CLI's discovery commands)
answered by v1's tool routes when v1 is on for the key, in the catalog's layout."""

# ruff: noqa: F811 - `env` is the router tests' fixture, imported from test_v1_classic.

from __future__ import annotations

import json
from typing import Any

import pytest

from tamarind import catalog
from tamarind._v1 import catalog as on_v1
from tamarind.errors import NotFoundError
from tamarind.http import HTTPClient

from test_v1_classic import FakeClassic, classic_calls, env, problem, same_output  # noqa: F401

LONG = "x" * 200


def tool(name: str, **extra: Any) -> dict[str, Any]:
    return {
        "name": name, "displayName": name.title(), "description": f"{name} does things", "modalities": ["protein"],
        "functions": ["structure-prediction"], "finetune": False, "custom": False, "requiredSettings": [],
        "timingPredictability": None, "docsUrl": None, "outputTypes": [], **extra,
    }


V1_TOOLS = [
    tool("esmfold", outputTypes=["pdb", "sequence"], description=LONG),
    tool("boltz", modalities=["protein", "small-molecule"], functions=["structure-prediction", "protein-ligand-docking"]),
    tool("admet", displayName="ADMET", modalities=["Small-Molecule"], functions=["small-molecule-property-prediction"]),
]


@pytest.fixture
def tool_set_on_v1(monkeypatch):
    """The tool set's switch (the list and its facets), turned on: it is held on the
    catalog by default."""
    monkeypatch.setattr(on_v1, "TOOL_SET_ON_V1", True)


def pages(**kw: Any) -> dict[str, Any]:
    """listTools in two pages, the way v1 pages it."""
    return {"items": V1_TOOLS[:2], "nextCursor": "c2"} if not kw.get("cursor") else {"items": V1_TOOLS[2:], "nextCursor": None}


# -- catalog/tools ------------------------------------------------------------------------


def test_the_tool_set_is_held_on_the_catalog_by_default(env):
    """Until the tool set is decided (v1 lists the app's tools and counts its facets from
    them), the list, modalities and functions stay on the catalog; schemas are v1's."""
    assert on_v1.TOOL_SET_ON_V1 is False
    for path in ("catalog/tools", "catalog/modalities", "catalog/functions"):
        FakeClassic.answers[path] = {}
    env.v1.answers["tools.schema"] = SCHEMA
    env.v1.answers["tools.get"] = TOOL_FACTS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        catalog.list_tools(client, search="fold")
        catalog.list_modalities(client)
        catalog.list_functions(client)
        catalog.get_schema(client, "boltz")
    assert [c[1] for c in classic_calls()] == ["catalog/tools", "catalog/modalities", "catalog/functions"]
    assert [c[0] for c in env.v1.calls] == ["tools.schema", "tools.get"]


def test_the_full_listing_is_every_page_summarized_and_sorted_by_name(env, tool_set_on_v1):
    env.v1.answers["tools.list"] = pages
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        out = catalog.list_tools(client)
    assert classic_calls() == []
    assert env.v1.calls == [("tools.list", (), {"cursor": None, "limit": 200}), ("tools.list", (), {"cursor": "c2", "limit": 200})]
    assert out == {
        "totalTools": 3,
        "filters": {"modality": None, "function": None, "search": None},
        "descriptionsOmitted": True,
        "availableCategories": ["Small-Molecule", "protein", "small-molecule"],
        "availableTags": ["protein-ligand-docking", "small-molecule-property-prediction", "structure-prediction"],
        "tools": [
            {"name": "admet", "displayName": "ADMET", "categories": ["Small-Molecule"]},
            {"name": "boltz", "displayName": "Boltz", "categories": ["protein", "small-molecule"]},
            # outputTypes only when the tool declares some, as the catalog omits an empty one
            {"name": "esmfold", "displayName": "Esmfold", "categories": ["protein"], "outputTypes": ["pdb", "sequence"]},
        ],
        "hint": on_v1.LIST_HINT + on_v1.FULL_LIST_HINT,
    }


def test_a_narrowed_listing_carries_tags_and_cut_descriptions(env, tool_set_on_v1):
    env.v1.answers["tools.list"] = pages
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        out = catalog.list_tools(client, modality="SMALL-molecule")  # matched in any case
    assert [t["name"] for t in out["tools"]] == ["admet", "boltz"]
    assert out["tools"][1] == {
        "name": "boltz", "displayName": "Boltz", "categories": ["protein", "small-molecule"],
        "tags": ["structure-prediction", "protein-ligand-docking"], "description": "boltz does things",
    }
    assert out["descriptionsOmitted"] is False and out["hint"] == on_v1.LIST_HINT
    assert out["filters"] == {"modality": "SMALL-molecule", "function": None, "search": None}
    # The facet lists are the whole catalog's, before narrowing.
    assert out["availableTags"] == ["protein-ligand-docking", "small-molecule-property-prediction", "structure-prediction"]
    # The filter is applied here, on the whole list, so the narrowing is the catalog's.
    assert all("modality" not in c[2] for c in env.v1.calls)


def test_search_matches_name_display_name_or_description(env, tool_set_on_v1):
    env.v1.answers["tools.list"] = pages
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        assert [t["name"] for t in catalog.list_tools(client, search="admet")["tools"]] == ["admet"]
        assert [t["name"] for t in catalog.list_tools(client, search="BOLTZ DOES")["tools"]] == ["boltz"]
        out = catalog.list_tools(client, search="xxxx", function="structure-prediction")
    assert [t["name"] for t in out["tools"]] == ["esmfold"]
    assert len(out["tools"][0]["description"]) == on_v1.DESCRIPTION_CHARS


def test_an_unrecognized_filter_value_is_named(env, tool_set_on_v1):
    env.v1.answers["tools.list"] = pages
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        out = catalog.list_tools(client, function="structure prediction")
    assert out["tools"] == [] and out["totalTools"] == 0
    assert out["unrecognizedFilters"] == {"function": "structure prediction"}
    assert out["hint"].endswith(
        "NOTE: unrecognized filter value(s) {'function': 'structure prediction'} — these are not valid; "
        "call listModalities()/listTags() for valid values."
    )


def test_the_custom_tool_listing_stays_on_the_catalog(env, tool_set_on_v1):
    FakeClassic.answers["catalog/tools"] = {"tools": [], "totalTools": 0}
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        catalog.list_tools(client, custom=True)
    assert env.v1.calls == [] and classic_calls() == [("GET", "catalog/tools", {"modality": None, "function": None, "search": None, "custom": "true"})]


def test_tools_prints_the_same_with_either_api(env, tool_set_on_v1):
    env.v1.answers["tools.list"] = pages
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        FakeClassic.answers["catalog/tools"] = catalog.list_tools(client)
    same_output(env, "--json", "tools")
    same_output(env, "--no-json", "tools")


# -- catalog/modalities, catalog/functions ----------------------------------------------------

FACETS = {
    "modalities": [
        {"name": "antibody", "label": "Antibody", "description": "Antibody tools.", "toolCount": 2},
        {"name": "protein", "label": "Protein", "description": None, "toolCount": 2},
        {"name": "cryoem", "label": None, "description": None, "toolCount": 0},
    ],
    "functions": [{"name": "utilities", "label": "Utilities", "description": "Helpers.", "toolCount": 7}],
}


def test_modalities_and_functions_are_v1s_facets_in_the_catalogs_layout(env, tool_set_on_v1):
    env.v1.answers["tools.facets"] = FACETS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        modalities = catalog.list_modalities(client)
        functions = catalog.list_functions(client)
    assert modalities == {
        "modalities": [
            {"value": "antibody", "label": "Antibody", "toolCount": 2, "description": "Antibody tools."},
            {"value": "protein", "label": "Protein", "toolCount": 2},
            {"value": "cryoem", "label": "cryoem", "toolCount": 0},
        ],
        "descriptionsAvailable": True,
        "hint": on_v1.MODALITIES_HINT,
    }
    assert functions == {
        "functions": [{"value": "utilities", "label": "Utilities", "toolCount": 7, "description": "Helpers."}],
        "descriptionsAvailable": True,
        "hint": on_v1.FUNCTIONS_HINT,
    }
    assert classic_calls() == []


def test_modalities_print_the_same_with_either_api(env, tool_set_on_v1):
    env.v1.answers["tools.facets"] = FACETS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        FakeClassic.answers["catalog/modalities"] = catalog.list_modalities(client)
        FakeClassic.answers["catalog/functions"] = catalog.list_functions(client)
    same_output(env, "--no-json", "modalities")
    same_output(env, "--no-json", "functions")


# -- catalog/tools/{tool}/schema --------------------------------------------------------------

SCHEMA = {
    "tool": "boltz",
    "version": "v3",
    "outputTypes": ["pdb"],
    "outputs": [{"glob": "metrics.csv", "description": "Main results table."}],
    "outputContract": {
        "byTask": None, "mainCSV": "metrics.csv", "taskType": "predict",
        "columns": [{"name": "ptm", "type": "number", "displayName": "pTM", "description": "Fold.", "tasks": None, "units": None}],
    },
    "example": {"sequence": "MK", "addLigands": False},
    "schema": {
        "type": "object",
        "required": ["sequence"],
        "properties": {
            "sequence": {"type": "string", "title": "Sequence", "description": "Protein.", "examples": ["MK"], "x-tamarind-type": "sequence"},
            "addLigands": {"type": ["boolean", "string"], "title": "Add ligands", "default": False, "pattern": "^true$"},
            "numSamples": {"type": ["integer", "string"], "default": 1, "minimum": 1, "maximum": 10},
            "seed": {"type": ["integer", "string"], "minimum": -999999999999999, "maximum": 999999999999999},
            "version": {"type": "string", "enum": ["2.2.1", "1.0.0"], "default": "2.2.1", "x-tamarind-type": "dropdown"},
            "ligands": {"type": "array", "items": {"type": "string", "x-tamarind-type": "string", "examples": [["SAH"]]}},
        },
        "allOf": [{"if": {"properties": {"addLigands": {"const": True}}}, "then": {"required": ["ligands"]}}],
    },
}
TOOL_FACTS = tool("boltz", displayName="Boltz-2", description="Co-folding.", modalities=["protein"], functions=["structure-prediction"])


def test_a_schema_is_v1s_rebuilt_as_the_catalogs_parameter_list(env):
    env.v1.answers["tools.schema"] = SCHEMA
    env.v1.answers["tools.get"] = TOOL_FACTS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        out = catalog.get_schema(client, "boltz")
    assert env.v1.calls == [("tools.schema", ("boltz",), {}), ("tools.get", ("boltz",), {})] and classic_calls() == []
    assert out == {
        "jobType": "boltz",
        "displayName": "Boltz-2",
        "description": "Co-folding.",
        "parameters": [
            {"name": "sequence", "type": "sequence", "displayName": "Sequence", "descr": "Protein.", "required": True, "example": "MK"},
            {"name": "addLigands", "type": "boolean", "displayName": "Add ligands", "default": False},
            {"name": "numSamples", "type": "number", "default": 1, "lowerBound": 1, "upperBound": 10},
            {"name": "seed", "type": "number"},  # v1's stand-in bounds for "no bound" are left out
            {"name": "version", "type": "dropdown", "default": "2.2.1", "options": ["2.2.1", "1.0.0"]},
            # required on a branch (allOf: if addLigands then ligands), as the catalog flags it
            {"name": "ligands", "type": "string", "required": True, "example": ["SAH"]},
        ],
        "categories": ["protein"],
        "tags": ["structure-prediction"],
        "hint": on_v1.SCHEMA_HINT,
        "outputTypes": ["pdb"],
        "outputs": {"mainCSV": "metrics.csv", "taskType": "predict", "columns": [{"name": "ptm", "type": "number", "displayName": "pTM", "description": "Fold."}]},
        "exampleJob": {"jobName": "boltz-example", "type": "boltz", "settings": {"sequence": "MK", "addLigands": False}},
        "exampleJobNote": on_v1._example_note(False),
    }
    # The example is v1's, one task branch already, so nothing is pruned from it.
    assert catalog.example_settings(out) == {"sequence": "MK", "addLigands": False}
    assert catalog.required_param_names(out) == ["sequence", "ligands"]


def test_a_task_dependent_outputs_contract_carries_the_catalogs_note(env):
    by_task = {"score": {"mainCSV": "scores.csv", "taskType": "score", "generates": []}}
    env.v1.answers["tools.schema"] = {**SCHEMA, "outputContract": {**SCHEMA["outputContract"], "byTask": by_task}}
    env.v1.answers["tools.get"] = TOOL_FACTS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        outputs = catalog.get_schema(client, "boltz")["outputs"]
    assert outputs["byTask"] == by_task and outputs["byTaskNote"] == on_v1.BY_TASK_NOTE


def test_an_example_with_a_file_input_says_to_upload_it(env):
    env.v1.answers["tools.schema"] = {
        **SCHEMA, "example": {"pdbFile": "target.pdb"},
        "schema": {"type": "object", "properties": {"pdbFile": {"type": "string", "x-tamarind-type": "pdb"}}},
    }
    env.v1.answers["tools.get"] = TOOL_FACTS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        out = catalog.get_schema(client, "boltz")
    assert out["exampleJobNote"] == on_v1._example_note(True) and "upload them first" in out["exampleJobNote"]


def test_a_schema_without_an_example_or_outputs_leaves_them_out(env):
    env.v1.answers["tools.schema"] = {**SCHEMA, "example": {}, "outputTypes": [], "outputContract": None}
    env.v1.answers["tools.get"] = TOOL_FACTS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        out = catalog.get_schema(client, "boltz")
    assert not {"exampleJob", "exampleJobNote", "outputTypes", "outputs"} & set(out)


def test_a_custom_tools_schema_has_no_tool_facts(env):
    env.v1.answers["tools.schema"] = {**SCHEMA, "schema": {**SCHEMA["schema"], "description": "My tool."}}

    def get(name):
        raise problem(404, "tool_not_found")

    env.v1.answers["tools.get"] = get
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        out = catalog.get_schema(client, "my-tool")
    assert (out["displayName"], out["description"], out["categories"], out["tags"]) == ("my-tool", "My tool.", [], [])


def test_an_unknown_tool_is_the_catalogs_error_answer(env):
    def schema(name):
        raise problem(404, "tool_not_found")

    FakeClassic.answers["catalog/tools/nope/schema"] = {
        "error": "Tool 'nope' not found in standard or custom tools",
        "hint": "Use getAvailableTools() or getAvailableTools(custom=true) to see all available tools",
    }
    env.v1.answers["tools.schema"] = schema
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        assert catalog.get_schema(client, "nope") == FakeClassic.answers["catalog/tools/nope/schema"]
    classic = env.run("classic", "--json", "schema", "nope")
    v1 = env.run("v1", "--json", "schema", "nope")
    assert isinstance(v1.exception, NotFoundError) and isinstance(classic.exception, NotFoundError)
    assert (v1.exit_code, str(v1.exception)) == (classic.exit_code, str(classic.exception))


def test_any_other_refusal_is_v1s_error(env):
    def schema(name):
        raise problem(503, "service_unavailable")

    env.v1.answers["tools.schema"] = schema
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        with pytest.raises(Exception) as caught:
            catalog.get_schema(client, "boltz")
    assert getattr(caught.value, "status_code", None) == 503 and classic_calls() == []


def test_schema_prints_the_same_with_either_api(env):
    env.v1.answers["tools.schema"] = SCHEMA
    env.v1.answers["tools.get"] = TOOL_FACTS
    with HTTPClient("https://mcp.tamarind.bio", "test-key") as client:
        FakeClassic.answers["catalog/tools/boltz/schema"] = catalog.get_schema(client, "boltz")
    same_output(env, "--no-json", "schema", "boltz")
    same_output(env, "--json", "schema", "boltz")
    res = same_output(env, "--json", "schema", "boltz", "--example")
    assert json.loads(res.stdout) == {"type": "boltz", "settings": {"sequence": "MK", "addLigands": False}}


def test_the_sdks_tools_follow_the_switch(env, tool_set_on_v1):
    from tamarind import Tamarind

    env.v1.answers["tools.list"] = pages
    env.v1.answers["tools.schema"] = SCHEMA
    env.v1.answers["tools.get"] = TOOL_FACTS
    env.v1.answers["tools.facets"] = FACETS
    with Tamarind(api_key="test-key") as client:
        assert client.tools.list()["totalTools"] == 3
        assert client.tools.example("boltz") == {"sequence": "MK", "addLigands": False}
        assert client.tools.modalities()["modalities"][0]["value"] == "antibody"
        assert client.tools.functions()["functions"][0]["value"] == "utilities"
    assert classic_calls() == []
