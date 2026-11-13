# Architecture & no-drift design

The CLI, the [MCP server](https://mcp.tamarind.bio), and the web app are all
**thin clients** over the same platform. The CLI never re-implements business
logic; it only knows how to call four well-defined surfaces. This is what keeps
the CLI and the MCP from drifting as the platform evolves.

## Five surfaces, five single sources of truth

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

Custom Tool creation, source upload, build, Versions, logs, and cancellation
are generated from the website backend's dedicated public OpenAPI artifact:

```text
backend-owned custom-tools-v1.generated.json
  -> Git-object provenance verification
  -> vendored spec + lock
  -> openapi-python-client==0.28.4
  -> generated models/endpoints
  -> thin Tamarind transport and resource adapters
```

The Website owns the projection and its referenced-component closure. The CLI sync
verifies the exact producer repository, commit, path, and bytes before atomically
installing the spec, provenance lock, generated server metadata, and generated package.
CI regenerates with the pinned mature generator and rejects drift. The handwritten
layer contains only HTTP/error normalization and ergonomic resource composition; it
does not parse OpenAPI or maintain a second schema IR/compiler.

Direct HTTP mutations accept optional `If-Match`. The SDK/CLI resource layer still
supplies observed validators automatically, preserving stale-snapshot protection.
The generated endpoints reflect the optional wire contract; the resource facade
does not require users to manage headers.

The SDK owns archive-local concerns that only the client can decide safely:
deterministic ZIP construction, symlink and junction rejection, upload limits,
JSON parseability and top-level object shape, and warnings about the networkless
runtime. Archives use stored ZIP entries so source digests do not depend on a
platform zlib build. Modes are also platform-stable: `run.sh` and files beginning
with a shebang are executable, while all other files are regular. The backend owns
the evolving `config.json` business contract and
validates it before accepting a build. The SDK deliberately does not maintain a
second list of configuration fields, enums, or cross-field rules.

`CustomTool.build()` composes the existing requests: create upload, PUT the archive,
submit the digest-checked build request, and return a typed result containing the server's
action plus its durable Version. It adds no server-side
BuildRequest, queue, lease, claim, or repair state. An ambiguous build response
is retried with the same caller-selected `Idempotency-Key`, or handled by listing Versions when
the caller did not supply one.

The resource layer uses the returned numbered `Version.version`, such as `v3`,
to select exact reads, logs, cancellation, and publication. Opaque, server-issued
Tool and Version ETags remain the identity and mutation validators.

The generated contract and public SDK signatures use standard `If-Match`. At the
final HTTP adapter boundary, the CLI forwards that value as
`X-Tamarind-If-Match`: Vercel otherwise evaluates the original request field
against the post-mutation response ETag and can replace a committed success with
an edge-generated 412. This transport-only compatibility spelling does not change
the validator or stale-write semantics and is deliberately absent from OpenAPI.

### 4. Pipelines read surface — source of truth: the public OpenAPI artifact

`Tamarind().pipelines` reads a run and pages through the molecules produced by one
of its node runs. The sync script selects only those operations and their referenced
schemas from the website backend's frozen public OpenAPI artifact, verifies the exact
producer Git object, and records that commit in a dedicated lock. Keeping this
projection separate prevents Pipelines changes from broadening or perturbing the
Custom Tools contract.

Generated endpoint code owns URL encoding and wire-model parsing. A small resource
adapter adds strict runtime checks and composes `PipelineRun` → `NodeRun` → molecule
pages without introducing another public vocabulary.

### 5. Agent API surface — source of truth: the agent's published OpenAPI spec

`Tamarind().agent` and `tamarind chat` drive the AI agent: chats (campaign mode
included), replies and their event stream, approvals, questions, files, subagents,
workflows, campaign collections and usage. The contract is tamarind-agent's
`docs/public-api/openapi.yaml`, vendored byte-for-byte as `openapi/agent-v1.yaml` with
its producer commit and SHA-256 in `openapi/agent-v1.lock.json`. Requests go to the same
host and `x-api-key` as the jobs API, with `Tamarind-Version: 2026-11-01` on every one.

The client is hand-written, not generated: the pinned generator emits no endpoint for
this spec (it refuses the date-typed `Tamarind-Version` header every path takes) and
drops `Message`/`Approval`. Drift is caught instead by
`tests/test_agent_api_contract.py`, which reads the vendored spec and fails when:

- an `operationId` is added, removed, or changes method, path or `Idempotency-Key`
  (each maps to one row of `src/tamarind/agent/_contract.py` and one SDK method);
- the `EventType` enum changes;
- a model schema names a property the matching dataclass does not read;
- an SDK call does not hit its operation's path, or cannot parse the spec's own example.

Re-sync: `git -C <tamarind-agent> show <sha>:docs/public-api/openapi.yaml >
openapi/agent-v1.yaml`, set `sourceCommit`/`artifactSha256` in the lock, and run the
contract test (with `TAMARIND_AGENT_CHECKOUT=<path>` it also checks the bytes are that
commit's).

The handwritten layer owns only what a client must: the retry policy (a 429 waits
`Retry-After`/`x-ratelimit-reset`; a lost response or 5xx is retried only where the
operation cannot apply twice), one `Idempotency-Key` per logical POST reused across its
retries, and the event stream, which resumes with `Last-Event-ID` after a cut or a
retryable `stream_interrupted` event, drops frames replayed at or before its cursor, and
skips unknown event types as the contract requires. Replies are always sent with
`stream: false` and followed on the events stream, because that one can be resumed and the
POST's own body cannot. Presigned upload and download URLs never receive the API key.

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
