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

## Custom tools

Author, deploy and publish your own tool without opening a browser.

```bash
# 1. Scaffold a folder (Dockerfile, run.sh, config.json) from the server's template
tamarind init my-esmfold
cd my-esmfold

# 2. Check locally — instant, and catches what would otherwise fail a build
tamarind check

# 3. Package the folder, upload it, build the image, stream the logs
tamarind deploy --create        # --create only matters the first time

# 4. Test the version you just built, not whatever is currently live
tamarind submit my-esmfold --set sequence=MKTAYIAK --wait --tool-version v1

# 5. Make it live for your org
tamarind publish
```

Everything else hangs off `ct`:

```bash
tamarind ct list                     # your org's tools
tamarind ct status my-esmfold        # latest build, live version
tamarind ct versions my-esmfold
tamarind ct logs my-esmfold          # reattach to a running build
tamarind ct config my-esmfold        # read config.json; --apply pushes it back
tamarind ct clone my-esmfold ./dir   # pull the source of an existing tool
```

A few things worth knowing:

- **The folder remembers its tool.** `init` writes `.tamarind` with the tool id, so
  `deploy` and `publish` need no arguments and a renamed directory still deploys to
  the right place. Commit it.
- **`deploy` is safe to re-run.** An unchanged folder reports `unchanged` and exits 0
  without building. Use `--fail-on-noop` in CI if you want that to be an error.
- **Credentials are never uploaded.** `.env`, key files and cloud credential
  directories are refused, and named in the output — the archive becomes an image
  layer, where a secret outlives deleting the file locally. Use
  `tamarind ct config --env` for values the tool needs at runtime.
- **The runtime container has no network.** Model weights belong in the image via the
  Dockerfile, not in the source upload.
- **`tamarind batch --tool-version`** submits up to 500 pinned runs at once. That path
  submits jobs independently rather than under a batch parent, and reports each one,
  so it exits non-zero if any item fails to dispatch even when the request succeeds.

The same lifecycle from Python is in
[`examples/custom_tool_e2e.py`](examples/custom_tool_e2e.py) — useful when you want
to decide something in between, such as only publishing a version whose smoke test
passed:

```python
from tamarind import customtools as ct

outcome = ct.build(client, name="my-esmfold", folder="./my-esmfold")
if outcome.deployed:                       # never infer this from outcome.path
    ct.publish(client, name="my-esmfold", version_name=outcome.version_name)
```

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
| Custom tools | `init`, `check`, `deploy`, `publish`, `ct list`, `ct status`, `ct versions`, `ct logs`, `ct cancel`, `ct config`, `ct clone`, `ct delete` |
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
