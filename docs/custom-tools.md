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

## Five-minute workflow

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

Run the lifecycle in this order:

```bash
# 1. Check whether the tool already exists.
tamarind --json custom-tools list

# 2. Validate locally. This does not authenticate, upload, or build anything.
tamarind --json custom-tools validate ./my-tool

# 3. Create the durable tool identity if it does not already exist.
tamarind --json custom-tools create my-tool --display-name "My Tool"

# 4. Package, upload, and build a Version, then wait for it to finish.
tamarind --json custom-tools build my-tool ./my-tool \
  --idempotency-key release-1 \
  --wait --timeout 1800 --poll-interval 10

# 5. Publish the completed Version using the opaque version.id from step 4.
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

`--wait` only bounds how long the local CLI waits. Exit code 7 means the local
timeout elapsed; the remote build may still be running. Do not start a new build
just because the local wait timed out. Reattach by Version ID instead:

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

Build timeout and failure errors retain `toolName`, `versionId`, `versionName`,
and `action` in their structured detail so an agent can recover the durable
Version and continue safely.

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
| `custom-tools list` | List visible tools | pagination options |
| `custom-tools get NAME` | Read one tool | — |
| `custom-tools create NAME` | Create a tool identity | `--display-name` |
| `custom-tools update NAME` | Change tool metadata | metadata options |
| `custom-tools validate FOLDER` | Validate local source without auth or upload | — |
| `custom-tools build NAME FOLDER` | Package, upload, and build a Version | `--idempotency-key`, `--wait`, `--timeout`, `--poll-interval` |
| `custom-tools versions NAME` | List a tool's Versions | pagination options |
| `custom-tools version NAME VERSION_ID` | Read or wait for one Version | `--wait`, `--timeout`, `--poll-interval` |
| `custom-tools logs NAME VERSION_ID` | Read paginated build logs | `--cursor` |
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
