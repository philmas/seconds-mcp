# SECONDS — Data Summary API + AI Agent Interface

A small, focused service that **summarizes tabular data** and lets an **AI agent**
query it in natural language — e.g. *"what was the average A1 response time in
September?"*

The sample dataset models the domain of the **SECONDS** ambulance-dispatch
software: each row is an emergency call with a region, an urgency class
(`A1`/`A2`/`B`) and a **response time in seconds** — the key performance metric
for ambulance services.

Three ways to reach the same summarization engine:

1. A **REST API** (FastAPI) with auto-generated OpenAPI docs at `/docs`.
2. An **MCP server** that exposes the summaries as tools, so Claude (Claude Code
   / Claude Desktop) can answer questions by calling them directly.
3. A **web dashboard** (Reflex + [buridan/ui](https://ui.buridan.dev)) with docs,
   database-grounded statistics + a reset button, and a live trace of every
   MCP / REST call.

## Quick start

One script bootstraps everything (virtualenv, dependencies, sample data) and
launches a service — Linux & macOS:

```bash
./start.sh          # REST API  → http://localhost:8000  (docs at /docs)
./start.sh web      # dashboard → http://localhost:3000
./start.sh mcp      # MCP server (stdio) for Claude
./start.sh test     # run the test suite
./start.sh setup    # just set up the venv + deps + data, don't launch
```

Prefer to do it by hand? See [Setup](#setup) below.

## Architecture

All query logic lives in a single core layer (`seconds/queries.py`); the REST
routes and the MCP tools are thin wrappers over it — one implementation, two
front doors. The Python core lives at the root; the whole web UI is isolated
under `web/`.

```
seconds/            # CORE — the summarization engine (API + MCP share it)
  schema.py         #   column metadata + validation whitelists (the safety net)
  db.py             #   read-only SQLite connection helper
  queries.py        #   list_schema, distinct_values, summarize, group_by, trend
  models.py         #   Pydantic request/response models + enums
  api.py            #   FastAPI app (thin routes)
  mcp_server.py     #   FastMCP server (thin tools)
  stats.py          #   grounded headline statistics for the dashboard
  call_log.py       #   trace log (separate DB) for MCP + REST calls
seed/generate_data.py   # sample-data generator (fresh random data each run)
tests/                  # unit tests (core) + API tests (TestClient)
data/                   # generated SQLite databases (git-ignored)
web/                    # Reflex + buridan/ui web UI — self-contained
  rxconfig.py       #   Reflex config (run `reflex run` from here)
  dashboard/        #   the app: pages (docs / database / logs) + state
  components/       #   buridan/ui component kit
  blocks/           #   buridan/ui example blocks
  assets/           #   static assets + globals.css
start.sh                # one-command launcher (see Quick start)
```

**Safety:** column and aggregation *names* are validated against a whitelist in
`schema.py` before any SQL is built; filter *values* are always bound
parameters; and query connections are opened read-only. So a request can never
inject SQL or mutate data.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Generate the sample database (data/seconds.db)
python -m seed.generate_data
```

## Run the REST API

```bash
uvicorn seconds.api:app --reload
```

Open <http://localhost:8000/docs> for interactive docs. Examples:

```bash
# Discover the schema
curl localhost:8000/schema

# Average A1 response time in September
curl -X POST localhost:8000/summarize -H 'Content-Type: application/json' -d '{
  "metric": "avg",
  "column": "response_time_seconds",
  "filters": {"urgency": "A1", "date_from": "2025-09-01", "date_to": "2025-09-30"}
}'

# Average response time per region
curl -X POST localhost:8000/group-by -H 'Content-Type: application/json' -d '{
  "metric": "avg", "group_by": "region", "column": "response_time_seconds"
}'

# Monthly response-time trend with a 3-month moving average
curl -X POST localhost:8000/trend -H 'Content-Type: application/json' -d '{
  "metric": "avg", "column": "response_time_seconds",
  "bucket": "month", "moving_average_window": 3
}'
```

### Endpoints

| Method & path                 | Purpose                                            |
|-------------------------------|----------------------------------------------------|
| `GET  /health`                | Liveness check                                     |
| `GET  /schema`                | Columns, roles, example values, available ops      |
| `GET  /columns/{col}/values`  | Distinct values of a categorical column            |
| `POST /summarize`             | Single aggregate (avg/sum/min/max/count) + filters |
| `POST /group-by`              | Aggregate grouped by a dimension or time bucket    |
| `POST /trend`                 | Time-series with optional moving average           |

## Hook up the AI agent (MCP)

The MCP server exposes five tools — `list_schema`, `list_column_values`,
`summarize`, `group_by`, `trend` — over stdio.

Try it standalone with the MCP Inspector:

```bash
mcp dev seconds/mcp_server.py
```

Register it with **Claude Code**. Use the **absolute path to this project's venv
Python** so the `mcp`/`fastapi`/`seconds` packages are importable (bare `python`
may resolve to a different interpreter without the dependencies):

```bash
claude mcp add seconds -- "$(pwd)/.venv/bin/python" -m seconds.mcp_server
```

> If you move the project or recreate the venv, re-run this command so the path
> stays correct.

…or add it to a **Claude Desktop** config (`claude_desktop_config.json`). Use the
absolute path to this project's Python (the venv) so `seconds` is importable:

```json
{
  "mcpServers": {
    "seconds": {
      "command": "/absolute/path/to/folder/.venv/bin/python",
      "args": ["-m", "seconds.mcp_server"]
    }
  }
}
```

Then ask, in natural language:

> *"What was the average A1 response time in September, and how does it compare
> per region?"*

The agent discovers the schema via `list_schema`, then calls `summarize` /
`group_by` with the right column and filters and explains the result.

## Web dashboard

A [Reflex](https://reflex.dev) + [buridan/ui](https://ui.buridan.dev) app with
three pages:

- **Docs** — installation, features, how-to, and a schema table rendered live
  from `seconds/schema.py`.
- **Database** — headline statistics computed live from the database, plus a
  **Reset / reinitialize** button. Each reset regenerates a fresh random
  dataset; the live statistics recompute from it, so they stay the ground truth
  you can validate the agent's answers against.
- **Logs** — a newest-first trace of every MCP tool call and REST request
  (source, arguments, status, duration).

```bash
./start.sh web                # easiest: bootstraps + launches the dashboard

# …or by hand:
pip install -e ".[ui]"        # Reflex + buridan/ui (one-time)
python -m seed.generate_data  # ensure data/seconds.db exists
cd web && reflex run          # dashboard at http://localhost:3000
```

The whole web UI is self-contained under `web/`, so `reflex run` is invoked
from there. The dashboard imports the `seconds` core directly (no HTTP hop).
Call logging is written to a **separate** database (`data/seconds_logs.db`), so
it survives a database reset and never touches the read-only incidents data.

> **Backend server:** this project pins `REFLEX_USE_GRANIAN=false` (see
> `web/.env`) so Reflex serves its backend with **uvicorn**. Granian's Rust/pyo3
> layer panics on state events in this version; uvicorn avoids it. The buridan
> components were added with `buridan init && buridan apply --preset b0 &&
> buridan add ...` and live in `web/components/` and `web/blocks/`.

## Tests

```bash
pytest -q
```

Tests build a small database with known values and assert exact aggregates
(including that `date_to` is inclusive and that invalid columns/metrics are
rejected).

## Out of scope (next steps)

Auth, pagination, write endpoints, multi-table joins and deployment were left
out to keep this focused; the layered structure leaves room to add them.
