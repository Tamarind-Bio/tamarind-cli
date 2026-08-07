# Architecture & no-drift design

The CLI, the [MCP server](https://mcp.tamarind.bio), and the web app are all
**thin clients** over the same platform. The CLI never re-implements business
logic; it only knows how to call two well-defined surfaces. This is what keeps
the CLI and the MCP from drifting as the platform evolves.

## One shape per resource

Every resource package has the same four layers, so learning one teaches the others:

| | |
|---|---|
| `wire` | the boundary. Raw payloads in, frozen types out. The only code that knows what an API payload looks like. |
| `api` | one function per endpoint. Client in, payload out, no branching. |
| `plan` | pure decisions. No network, no clock, no filesystem. |
| `flow` | orchestration that owns the clock. Reports progress through callbacks, never by printing. |

```
jobs/     wire · api · plan · flow
files/    wire · api · plan
catalog/  wire · api · plan
```

Shared infrastructure sits alongside: `http` (transport), `config` (credentials and
profiles), `errors` (one hierarchy, each carrying a stable exit code), `upload`
(streaming PUT to a presigned URL), `redact` (stripping credential-bearing URLs out
of payloads).

These are not conventions to remember — [`tests/test_layering.py`](../tests/test_layering.py)
enforces them: nothing below `cli/` imports typer or writes to a stream, `plan` and
`wire` reach for no I/O layer or clock, response-shape keys appear only in `wire`, and
every error declares its own distinct exit code. They are guardrails against drift
rather than a sandbox, but they fail loudly when the shape slips.

## Two surfaces, two single sources of truth

### 1. Job/file REST surface — source of truth: the OpenAPI spec

`submit`, `validate`, `batch`, `jobs`, `status`/`wait`, `results`, `files`,
`cancel`, and `delete` map onto operations in `openapi-mcp.yaml` — the same
server contract used to generate the MCP surface. The mapping lives in each
resource's `api` module — [`jobs/api.py`](../src/tamarind/jobs/api.py) and
[`files/api.py`](../src/tamarind/files/api.py) — each intentionally a small,
branch-free mapping of those operations.

([`rest.py`](../src/tamarind/rest.py) is the pre-split namespace that mixed both
resources. It survives as a deprecated shim re-exporting from the new homes; new
code should not use it.)

The CLI mapping is still client code and can drift. Unit tests cover request and
response shapes, and authenticated no-spend smoke tests should exercise auth,
catalog lookup, schema lookup, and validation before a release. Changes to the
server contract should update the CLI tests in the same change or release train.

These calls go directly to the job API (`https://app.tamarind.bio/api/`) with
the `x-api-key` header.

### 2. Discovery surface — source of truth: a shared catalog module

`tools`, `modalities`, `functions`, and `schema` need per-org visibility logic
(which tools an account may see, per-parameter gating, example generation) that
must run server-side. So the CLI does **not** read the catalog database; it
calls the `/catalog/*` HTTP routes ([`catalog/api.py`](../src/tamarind/catalog/api.py)),
which return exactly the JSON the MCP's discovery tools return.

The MCP tools and the `/catalog/*` routes are served by the **same shared
implementation**, so a tool looks identical no matter which client you use.
Because the logic lives in one module, *where* discovery is hosted (the MCP host
today; potentially the main API or a dedicated service later) is a deployment
detail that can change without any client change and without drift.

## Why not a single binary that re-encodes the API?

A from-scratch client in another language would re-encode the request shapes and
the catalog logic — two copies that drift the moment the platform changes.
Keeping the CLI thin and anchored to the same OpenAPI contract (and,
server-side, the same catalog module) reduces drift and makes it testable. It
does not eliminate the need for compatibility tests and coordinated releases.

## Configuration indirection

Endpoints are configurable (`--api-base`, `--catalog-base`, profiles), so the
same binary points at prod or staging, and the discovery host can move later
without a new release.
