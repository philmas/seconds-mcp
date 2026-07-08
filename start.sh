#!/usr/bin/env bash
#
# SECONDS — one-command launcher for Linux & macOS.
#
# Bootstraps a virtualenv, installs dependencies, seeds the sample database,
# and starts the service you ask for.
#
#   ./start.sh            # REST API (http://localhost:8000, docs at /docs)
#   ./start.sh api        #    same as above
#   ./start.sh web        # Reflex dashboard (http://localhost:3000)
#   ./start.sh mcp        # MCP server (stdio) for Claude
#   ./start.sh test       # run the test suite
#   ./start.sh setup      # just create the venv, install deps, seed data
#
set -euo pipefail

# Always operate from the project root (the directory this script lives in),
# so it works no matter where it is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$SCRIPT_DIR"

VENV="$SCRIPT_DIR/.venv"
PY="$VENV/bin/python"

info() { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }

# --- bootstrap helpers ----------------------------------------------------- #

ensure_venv() {
  if [ ! -x "$PY" ]; then
    local boot
    boot="$(command -v python3 || command -v python || true)"
    if [ -z "$boot" ]; then
      echo "Error: Python 3 not found on PATH. Install Python 3.10+ first." >&2
      exit 1
    fi
    info "Creating virtual environment (.venv)…"
    "$boot" -m venv "$VENV"
    "$PY" -m pip install --upgrade pip >/dev/null
  fi
}

# ensure_deps <import-name> <pip-extras>
# Installs the project (editable) with the given extras only if <import-name>
# is not already importable — so repeat runs start instantly.
ensure_deps() {
  local module="$1" extras="$2"
  if ! "$PY" -c "import $module" >/dev/null 2>&1; then
    info "Installing dependencies (${extras})…"
    "$PY" -m pip install -e ".${extras}"
  fi
}

ensure_data() {
  if [ ! -f "$SCRIPT_DIR/data/seconds.db" ]; then
    info "Generating sample database (data/seconds.db)…"
    "$PY" -m seed.generate_data
  fi
}

# --- commands -------------------------------------------------------------- #

cmd="${1:-api}"
case "$cmd" in
  api)
    ensure_venv; ensure_deps seconds "[dev]"; ensure_data
    info "REST API → http://localhost:8000  (interactive docs at /docs)"
    exec "$PY" -m uvicorn seconds.api:app --reload
    ;;

  web|dashboard|ui)
    ensure_venv; ensure_deps reflex "[ui]"; ensure_data
    info "Dashboard → http://localhost:3000  (backend on :8001)"
    # Reflex reads .env from its run directory; the flag avoids the granian
    # panic (see web/.env). Exported here too as a belt-and-suspenders.
    export REFLEX_USE_GRANIAN=false
    cd "$SCRIPT_DIR/web"
    exec "$VENV/bin/reflex" run
    ;;

  mcp)
    ensure_venv; ensure_deps seconds "[dev]"; ensure_data
    info "MCP server on stdio (register with: claude mcp add seconds -- \"$PY\" -m seconds.mcp_server)"
    exec "$PY" -m seconds.mcp_server
    ;;

  test|tests)
    ensure_venv; ensure_deps seconds "[dev]"
    exec "$PY" -m pytest -q
    ;;

  setup)
    ensure_venv
    ensure_deps seconds "[dev]"
    ensure_deps reflex "[ui]"
    ensure_data
    info "Setup complete. Try: ./start.sh api   |   ./start.sh web"
    ;;

  -h|--help|help)
    sed -n '3,14p' "$0"
    ;;

  *)
    echo "Unknown command: $cmd" >&2
    echo "Usage: ./start.sh [api|web|mcp|test|setup]  (default: api)" >&2
    exit 1
    ;;
esac
