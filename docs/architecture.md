# Architecture & no-drift design

The CLI, the [MCP server](https://mcp.tamarind.bio), and the web app are all
**thin clients** over the same platform. The CLI never re-implements business
logic; it only knows how to call two well-defined surfaces. This is what keeps
the CLI and the MCP from drifting as the platform evolves.

## Two surfaces, two single sources of truth

### 1. Job/file REST surface — source of truth: the OpenAPI spec

`submit`, `validate`, `batch`, `jobs`, `status`/`wait`, `results`, `files`,
`cancel`, `delete` map 1:1 onto operations in `openapi-mcp.yaml` — the same
spec the MCP server is generated from (`FastMCP.from_openapi`). The CLI's
[`rest.py`](../src/tamarind/rest.py) is a literal, logic-free mapping of that
spec. Because both clients derive from one spec, a contract test can fail CI if
they diverge.

These calls go directly to the job API (`https://app.tamarind.bio/api/`) with
the `x-api-key` header.

### 2. Discovery surface — source of truth: a shared catalog module

`tools`, `modalities`, `functions`, and `schema` need per-org visibility logic
(which tools an account may see, per-parameter gating, example generation) that
must run server-side. So the CLI does **not** read the catalog database; it
calls the `/catalog/*` HTTP routes ([`catalog.py`](../src/tamarind/catalog.py)),
which return exactly the JSON the MCP's discovery tools return.

The MCP tools and the `/catalog/*` routes are served by the **same shared
implementation**, so a tool looks identical no matter which client you use.
Because the logic lives in one module, *where* discovery is hosted (the MCP host
today; potentially the main API or a dedicated service later) is a deployment
detail that can change without any client change and without drift.

## Why not a single binary that re-encodes the API?

A from-scratch client in another language would re-encode the request shapes and
the catalog logic — two copies that drift the moment the platform changes.
Keeping the CLI a thin, spec-derived Python client that shares the OpenAPI
contract (and, server-side, the catalog module) with the MCP makes drift a
structural impossibility plus a CI-enforced check, rather than something to
remember.

## Configuration indirection

Endpoints are configurable (`--api-base`, `--catalog-base`, profiles), so the
same binary points at prod or staging, and the discovery host can move later
without a new release.
