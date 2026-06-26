# Tamarind CLI

Command-line interface for the [Tamarind Bio](https://tamarind.bio) platform.
Discover tools, submit and monitor protein / nucleic-acid / small-molecule jobs,
and download results — from your terminal, a script, CI, or an AI coding agent
(Claude Code, Codex, …).

The CLI is a thin client over the same API the [Tamarind MCP
server](https://mcp.tamarind.bio) uses, so the two stay in lockstep. See
[`docs/architecture.md`](docs/architecture.md) for how drift is prevented.

## Install

```bash
curl -fsSL https://install.tamarind.bio/cli/install.sh | sh
```

Or with Python tooling:

```bash
uv tool install tamarind-cli      # or: pipx install tamarind-cli
```

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
tamarind schema boltz --example > job.yaml

# 3. Validate, then submit
tamarind validate boltz --input job.yaml
tamarind submit   boltz --input job.yaml --name my-run --wait --download ./out

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

## Output for agents

Every command emits JSON when stdout is not a TTY, or with `--json`. Exit codes
are stable: `0` ok, `3` auth, `4` not-found, `5` validation, `6` rate-limit.

```bash
tamarind jobs --json | jq '.jobs[] | select(.JobStatus=="Running")'
```

## Commands

| Group | Commands |
|---|---|
| Discover | `tools`, `modalities`, `functions`, `schema` |
| Submit | `validate`, `submit`, `batch` |
| Monitor | `jobs`, `status`, `wait`, `results`, `logs` |
| Files | `files list`, `files upload`, `files delete`, `files folders` |
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
