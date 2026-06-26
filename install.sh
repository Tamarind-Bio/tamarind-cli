#!/bin/sh
# Tamarind CLI installer.
#
#   curl -fsSL https://install.tamarind.bio/cli/install.sh | sh
#
# Installs the `tamarind` command into an isolated environment using whatever
# Python tooling is available (uv > pipx > pip --user). Override the package
# source with TAMARIND_CLI_SPEC (e.g. a local path or a git URL).
set -eu

SPEC="${TAMARIND_CLI_SPEC:-tamarind-cli}"

say()  { printf '\033[0;36m%s\033[0m\n' "$*"; }
warn() { printf '\033[0;33m%s\033[0m\n' "$*" >&2; }
die()  { printf '\033[0;31merror: %s\033[0m\n' "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

if have uv; then
  say "Installing $SPEC with uv…"
  uv tool install --force "$SPEC"
elif have pipx; then
  say "Installing $SPEC with pipx…"
  pipx install --force "$SPEC"
elif have python3; then
  say "Installing $SPEC with pip (--user)…"
  python3 -m pip install --user --upgrade "$SPEC"
else
  die "Need uv, pipx, or python3 on PATH. Install uv: https://docs.astral.sh/uv/"
fi

if have tamarind; then
  say "Installed: $(tamarind --version)"
  say "Next: export TAMARIND_API_KEY=... (or run 'tamarind auth login'), then 'tamarind tools'."
else
  warn "Installed, but 'tamarind' is not on PATH yet."
  warn "Add your tool bin dir to PATH (uv: 'uv tool update-shell'; pipx: 'pipx ensurepath')."
fi
