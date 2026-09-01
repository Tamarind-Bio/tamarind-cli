# Custom Tools CLI

The Custom Tools CLI, available in `tamarind-cli` 0.4.0 and later, takes a local
tool folder through validation, build, monitoring, and publication. It is useful
for a person working in a terminal, a CI job, or an agent with filesystem access.

## Install and authenticate

Install or upgrade the CLI and confirm the installed version:

```bash
uv tool install --upgrade tamarind-cli
tamarind --version
```

Authenticate with an API key from the Tamarind web app (Settings → API):

```bash
export TAMARIND_API_KEY="sk_..."  # recommended for agents and CI

# Or store the key in ~/.tamarind/config.json:
tamarind auth login
```

The examples below use `--json` so their output is stable for scripts and
agents. Global options such as `--json`, `--profile`, and `--api-base` must
appear before `custom-tools`.

## End-to-end workflow

Suppose the source is in `./my-tool` and has this typical shape:

```text
my-tool/
├── Dockerfile
├── run.sh
├── config.json
└── ...
```

`Dockerfile` is required. `run.sh` is strongly recommended because the runtime
invokes it directly. `config.json` is optional for local validation; when it is
present, it must be a JSON object and the server validates its full semantics.

Run the lifecycle in this order. First, validate locally. This step does not
authenticate, upload, or build anything:

```bash
tamarind --json custom-tools validate ./my-tool
```

Next, resolve the durable Tool identity with an exact lookup:

```bash
tamarind --json custom-tools get my-tool
```

Branch on that command's exit code before continuing:

| Exit | Meaning | Next step |
|---|---|---|
| `0` | The Tool exists and is visible | Reuse it; do not run `create` |
| `4` | The Tool was not found or is not visible | Confirm the name is unclaimed, then run `create` |
| any other nonzero value | Authentication, transport, or another failure | Stop and handle the error |

For a confirmed unclaimed name, create the identity once:

```bash
tamarind --json custom-tools create my-tool --display-name "My Tool"
```

Package, upload, and build a Version, then wait for monitoring to finish:

```bash
tamarind --json custom-tools build my-tool ./my-tool \
  --idempotency-key release-1 \
  --wait --timeout 1800 --poll-interval 10
```

Finally, publish the completed Version using the opaque `version.id` returned by
the build:

```bash
tamarind --json custom-tools publish my-tool VERSION_ID
```

A successful local validation returns:

```json
{"valid": true, "errors": [], "warnings": []}
```

A build result has this general shape:

```json
{
  "action": "build",
  "version": {
    "id": "0192d87e-12ab-7cde-9f01-23456789abcd",
    "name": "v3",
    "toolName": "my-tool",
    "status": "Complete",
    "terminal": true
  }
}
```

Always save and use `version.id` for exact Version operations. `version.name`
such as `v3` is a display label, not an endpoint identifier.

Use exact reads for identity checks: `custom-tools get NAME` for a Tool and
`custom-tools version NAME VERSION_ID` for a Version. The `list`, `versions`,
and `logs` commands each return one page; follow `nextCursor` with `--cursor`
until it is `null` when a complete collection or log stream is required.

Use an idempotency key for builds initiated by automation. If delivery of the
first response is ambiguous, retrying with the same key returns the already
admitted Version instead of starting a duplicate build.

## Runtime contract

The built tool runs with the following contract:

- The working directory is `/app`.
- Scalar inputs are supplied through environment variables.
- File inputs are mounted read-only under `/app/inputs/`.
- Write durable result files under `/app/out/`.
- Runtime network access is unavailable; include required weights and assets in
  the image or inputs.
- Network access is available while the image is built.

The local validator catches archive hazards, a missing `Dockerfile`, and basic
`config.json` syntax/shape problems before upload. The server remains
authoritative for the full configuration contract and build outcome.

## Monitor and reattach

For both `build --wait` and `version --wait`, `--timeout` starts when Version
monitoring begins. It does not include earlier work: local validation,
packaging, upload, and build admission for `build`, or the initial Tool and
Version reads for `version`. Use a process-level or CI deadline as well when the
entire CLI invocation must be bounded.

Exit code 7 means the monitoring timeout elapsed; the remote build may still be
running. Do not start a new build just because monitoring timed out. Reattach by
Version ID instead:

```bash
tamarind --json custom-tools version my-tool VERSION_ID \
  --wait --timeout 1800 --poll-interval 10
```

Read build logs, following the returned cursor when the response has another
page:

```bash
tamarind --json custom-tools logs my-tool VERSION_ID
tamarind --json custom-tools logs my-tool VERSION_ID --cursor NEXT_CURSOR
```

Once the CLI has a durable Version, monitoring timeout and failure errors retain
`toolName`, `versionId`, and `versionName` in their structured detail. Errors
from the initial `build --wait` monitoring phase also include `action`; errors
from a later `version --wait` reattachment do not. A failure before build
admission has returned a Version cannot provide this handle, which is why
automated builds should reuse their idempotency key after an ambiguous request.

## Publish and roll back

Publishing changes which completed Version is active. List Versions, inspect the
candidate, and publish its opaque ID:

```bash
tamarind --json custom-tools versions my-tool
tamarind --json custom-tools version my-tool VERSION_ID
tamarind --json custom-tools publish my-tool VERSION_ID
```

Rollback uses the same operation: publish the ID of an older known-good,
completed Version.

## Update, cancel, and delete

Inspect and update the tool metadata:

```bash
tamarind --json custom-tools get my-tool
tamarind --json custom-tools update my-tool --display-name "My Renamed Tool"
```

Cancellation and deletion are destructive. Non-interactive callers must pass
`--yes` explicitly:

```bash
tamarind --json custom-tools cancel my-tool VERSION_ID --yes
tamarind --json custom-tools delete my-tool --yes
```

If a mutation returns `412 Precondition Failed`, refetch the Tool or Version,
confirm the mutation is still appropriate, and retry with the refreshed state.

## Command reference

| Command | Purpose | Useful options |
|---|---|---|
| `custom-tools list` | Read one page of visible tools | `--limit`, `--cursor` |
| `custom-tools get NAME` | Read one tool | — |
| `custom-tools create NAME` | Create a tool identity | `--display-name` |
| `custom-tools update NAME` | Change tool metadata | metadata options |
| `custom-tools validate FOLDER` | Validate local source without auth or upload | — |
| `custom-tools build NAME FOLDER` | Package, upload, build, and optionally monitor a Version | `--idempotency-key`, `--wait`, monitoring `--timeout`, `--poll-interval` |
| `custom-tools versions NAME` | Read one page of a tool's Versions | `--limit`, `--cursor` |
| `custom-tools version NAME VERSION_ID` | Read or monitor one exact Version | `--wait`, monitoring `--timeout`, `--poll-interval` |
| `custom-tools logs NAME VERSION_ID` | Read one page of build logs | `--cursor` |
| `custom-tools cancel NAME VERSION_ID` | Cancel an active build | `--yes` |
| `custom-tools publish NAME VERSION_ID` | Make a completed Version active | — |
| `custom-tools delete NAME` | Delete a tool | `--yes` |

Run `tamarind custom-tools COMMAND --help` for every option and default.

## CLI and MCP

The CLI and MCP are peer adapters over the public Tamarind API:

```text
                         ┌─ Python SDK ─ CLI
Public Custom Tools API ─┤
                         └─ async HTTP adapter ─ MCP
```

The MCP server does not shell out to the CLI. Both surfaces use the same public
contract, but they fit different execution environments:

- Use the CLI for local folders, shell scripts, CI, and agents with filesystem
  and process access.
- Use MCP for remotely authenticated agents. Its equivalent lifecycle tools are
  `deployCustomTool` and `getCustomTool`.

GitHub connection and push-to-deploy authorization are not part of the 0.4.0
release. The supported CLI path starts from a local source folder.
