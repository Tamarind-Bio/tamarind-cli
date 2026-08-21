# Architecture & no-drift design

The CLI, the [MCP server](https://mcp.tamarind.bio), and the web app are all
**thin clients** over the same platform. The CLI never re-implements business
logic; it only knows how to call three well-defined surfaces. This is what keeps
the CLI and the MCP from drifting as the platform evolves.

## Three surfaces, three single sources of truth

### 1. Job/file REST surface — source of truth: the OpenAPI spec

`submit`, `validate`, `batch`, `jobs`, `status`/`wait`, `results`, `files`,
`cancel`, and `delete` map onto operations in `openapi-mcp.yaml` — the same
server contract used to generate the MCP surface. The CLI's
[`rest.py`](../src/tamarind/rest.py) is intentionally a small mapping of those
operations.

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
calls the `/catalog/*` HTTP routes ([`catalog.py`](../src/tamarind/catalog.py)),
which return exactly the JSON the MCP's discovery tools return.

The MCP tools and the `/catalog/*` routes are served by the **same shared
implementation**, so a tool looks identical no matter which client you use.
Because the logic lives in one module, *where* discovery is hosted (the MCP host
today; potentially the main API or a dedicated service later) is a deployment
detail that can change without any client change and without drift.

### 3. Custom Tools surface — source of truth: the public OpenAPI artifact

Custom Tool creation, source upload, version builds, logs, cancellation, and
publication are generated from the website backend's public OpenAPI artifact.
The committed SDK input is the byte-identical Custom Tools artifact generated
and reviewed in the website repository; this repository performs no independent
route or schema extraction. `openapi/custom-tools-v1.provenance.json` pins the
exact website commit, source path, and SHA-256 digest. CLI CI validates that
metadata locally; website release verification fetches the pinned public CLI
revision and compares both repositories byte-for-byte.

The SDK owns archive-local concerns that only the client can decide safely:
deterministic ZIP construction, symlink and junction rejection, upload limits,
JSON parseability and top-level object shape, and warnings about the networkless
runtime. The backend owns the evolving `config.json` business contract and
validates it before accepting a build. The SDK deliberately does not maintain a
second list of configuration fields, enums, or cross-field rules.

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
