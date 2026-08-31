# Tamarind CLI

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

Command-line interface for the [Tamarind Bio](https://tamarind.bio) platform.
Discover tools, submit and monitor protein / nucleic-acid / small-molecule jobs,
and download results — from your terminal, a script, CI, or an AI coding agent
(Claude Code, Codex, …).

The CLI is a thin client over the same API the [Tamarind MCP
server](https://mcp.tamarind.bio) uses, so the two stay in lockstep. See
[`docs/architecture.md`](docs/architecture.md) for how drift is prevented.

## Install

```bash
uv tool install tamarind-cli      # or: pipx install tamarind-cli
```

Or with the bootstrap installer (uses `uv`, `pipx`, or Python/pip already on
your `PATH`):

```bash
curl -fsSL https://app.tamarind.bio/cli/install.sh | sh
```

To track the repo directly instead of the PyPI release:

```bash
uv tool install "git+https://github.com/Tamarind-Bio/tamarind-cli"
# or: pipx install "git+https://github.com/Tamarind-Bio/tamarind-cli"
```

> Releasing: tag a GitHub Release and the [`publish.yml`](.github/workflows/publish.yml)
> workflow builds and uploads to PyPI via Trusted Publishing (configure the
> trusted publisher for `tamarind-cli` on PyPI first).

## Authenticate

Get an API key from the Tamarind web app (Settings → API), then either:

```bash
export TAMARIND_API_KEY="sk_..."      # best for agents / CI
# or
tamarind auth login                    # stores it in ~/.tamarind/config.json
tamarind auth status
```

## Quickstart

```bash
# 1. Find a tool
tamarind tools --function structure-prediction --modality protein
tamarind tools --search boltz

# 2. Inspect its parameters and grab a runnable example
tamarind schema boltz
tamarind schema boltz --example > job.yaml   # most tools ship an example; some don't

# 3. Validate, then submit
tamarind validate boltz --input job.yaml
tamarind submit boltz --input job.yaml --name my-run \
  --wait --timeout 3600 --download ./out

# 4. Monitor / fetch
tamarind jobs
tamarind status my-run
tamarind results my-run --download ./out
```

Set individual fields inline instead of a file:

```bash
tamarind submit boltz \
  --set inputFormat=sequence \
  --set sequence=MKTVRQERLKSIVRIL... \
  --name quick-fold
```

## Python SDK

The package exposes typed Pipelines and Custom Tools resources. Pipeline runs use
the same node-run terminology as the web app and public REST API:

```python
from tamarind import Tamarind

with Tamarind() as client:
    run = client.pipelines.get_run("run-id")
    for node_run in run.node_runs:
        page = node_run.molecules(limit=100)
        print(node_run.label, page.items)
```

The Custom Tools resource checks archive-local
safety, packages a folder, uploads it directly to object storage, and submits the
digest-checked build request. The server
remains authoritative for source readiness, Versions, logs, and the evolving
`config.json` contract.

```python
from tamarind import Tamarind
from tamarind.errors import CustomToolNotFoundError

with Tamarind() as client:
    try:
        tool = client.custom_tools.get("my-esmfold")
    except CustomToolNotFoundError:
        tool = client.custom_tools.create("my-esmfold", display_name="My ESMFold")

    result = tool.build("./my-esmfold", idempotency_key="release-2026-08-26")
    print(result.action)  # build, reuse_image, or unchanged
    version = result.version
    print(version.id, version.name)  # opaque machine identity, human-facing label
    if not version.terminal:
        version = version.monitor(timeout=1800, on_event=print)
```

`build()` returns a typed result describing what the request did and the durable
Version it produced. It is convenience orchestration, not a durable request
object. Reuse `idempotency_key` when retrying an ambiguous build response; the
server returns the already admitted Version. If no key was supplied, fetch the
tool's versions before retrying. Interrupting `monitor()` stops local monitoring; it
does not cancel the remote build.

Connect a GitHub repository as the tool's source and wait for the initial import:

```python
from tamarind.errors import CustomToolGitHubAuthorizationRequiredError

try:
    connection = tool.connect_github(
        "acme/my-esmfold",
        branch="main",
        auto_publish=True,
    )
except CustomToolGitHubAuthorizationRequiredError as authorization:
    print(f"Authorize GitHub in your browser: {authorization.authorization_url}")
    input("Press Enter after authorization completes...")
    connection = authorization.resume()

connection = connection.monitor(timeout=600)
print(connection.commit)

current = tool.github_connection()  # None when disconnected
tool.refresh().disconnect_github()  # imported source and Versions remain
```

If the Tamarind GitHub App already has access, `connect_github()` returns
immediately without the authorization step. Otherwise the exception contains a
short-lived, opaque resume token bound to the exact Tool generation, repository,
branch, options, organization, and API identity. `resume()` retries only that
original operation; it does not require an installation ID or expose one to the
caller. Future pushes to the selected branch synchronize and build automatically.
A monitoring timeout stops only the local wait, not the server-side import.

Exact Version operations use `version.id`; `version.name` is display-only. If a
mutation reports `412 Precondition Failed`, refetch the affected Tool or Version,
confirm the mutation is still desired, and retry using the refreshed resource.

The same lifecycle is available through the unified CLI. A typical release is:

```bash
tamarind custom-tools validate ./my-esmfold
tamarind custom-tools create my-esmfold --display-name "My ESMFold"
tamarind custom-tools build my-esmfold ./my-esmfold \
  --idempotency-key release-2026-08-31 --wait --timeout 1800
tamarind custom-tools versions my-esmfold
tamarind custom-tools publish my-esmfold <opaque-version-id>
```

Build responses contain both a display name such as `v3` and an opaque `id`.
Pass the opaque ID to `version`, `logs`, `cancel`, and `publish`. A local wait
timeout does not cancel the remote build; reattach with
`tamarind custom-tools version NAME VERSION_ID --wait`.

## Output for agents

Every command emits JSON when stdout is not a TTY, or with `--json`. Result
documents are written to stdout. Typed command, transport, and usage errors are
written to stderr as
`{"error":{"type":...,"message":...,"exitCode":...,"detail":...}}`; `detail`
is omitted when unavailable. A domain verdict can deliberately combine a
nonzero exit with a result document: invalid `validate` output remains on
stdout with exit 5, and a terminal unsuccessful job remains on stdout with exit
9 so callers can inspect its status. Exit codes are stable: `0` ok, `1`
generic failure, `2` usage, `3` auth, `4` not-found, `5` validation, `6`
rate-limit, `7` timeout (a bounded wait elapsed while the remote job may still
run), `8` budget/quota exhaustion, and `9` remote job failure.

For agent workflows, always put a deadline on blocking commands. `submit --wait`
and `results --wait` accept `--timeout`; the standalone `wait` command remains
the easiest way to reattach to a durable job name.

Starting in 0.2, `results` requires `--download DIR` by default and never prints
a presigned URL implicitly. This intentional safety boundary is why the release
uses a new pre-1.0 minor version. The explicit `--show-url` escape hatch returns
a credential-bearing, short-lived URL; do not use it in agent, CI, or shared logs.

Not every tool ships a runnable example — `schema <tool> --example` exits non-zero
(with a clear message) when one isn't available, so a `> job.yaml` redirect never
silently produces an empty file. Destructive commands (`delete`, `files delete`)
require `--yes`/`-y` when run non-interactively (piped or `--json`), so an agent
never removes data without an explicit confirmation.

```bash
tamarind --json jobs | jq '.jobs[] | select(.JobStatus=="Running")'
```

`--json`, `--profile`, and the endpoint/auth overrides are global options, so
place them before the command name.

## Commands

| Group | Commands |
|---|---|
| Discover | `tools`, `modalities`, `functions`, `schema` |
| Submit | `validate`, `submit`, `batch` |
| Monitor | `jobs`, `status`, `wait`, `results`, `logs` |
| Files | `files list`, `files stats`, `files upload`, `files delete`, `files folders` |
| Custom Tools | `custom-tools list`, `get`, `create`, `update`, `validate`, `build`, `versions`, `version`, `logs`, `cancel`, `publish`, `delete` |
| Lifecycle | `cancel`, `delete` |
| Auth | `auth login`, `auth status`, `auth logout` |

Run `tamarind <command> --help` for full options.

## Configuration

| Setting | Flag | Env var | Default |
|---|---|---|---|
| API key | `--api-key` | `TAMARIND_API_KEY` | — |
| Job API base | `--api-base` | `TAMARIND_API_BASE` | `https://app.tamarind.bio/api/` |
| Catalog base | `--catalog-base` | `TAMARIND_CATALOG_BASE` | `https://mcp.tamarind.bio` |
| Profile | `--profile` | `TAMARIND_PROFILE` | `default` |

Profiles (key + endpoints) are stored in `~/.tamarind/config.json`. Use a
profile to point at staging:

```bash
tamarind --profile staging --api-base https://staging.tamarind.bio/api/ auth login
TAMARIND_PROFILE=staging tamarind tools
```

## Links

- [CLI docs](https://app.tamarind.bio/api-docs/cli) — the hosted quickstart and command reference
- [MCP server](https://app.tamarind.bio/api-docs/mcp-server) — the hosted option for claude.ai, ChatGPT, and other MCP clients
- [API key](https://app.tamarind.bio/api-docs/api-key) — get your key and review rate limits

Questions or need help? Contact us at [info@tamarind.bio](mailto:info@tamarind.bio).

## License

Licensed under the [Apache License 2.0](LICENSE).
