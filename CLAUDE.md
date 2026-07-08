# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

**SECONDS** — a simple data-summarization API + MCP server over a SQLite database
of ambulance-dispatch data (`incidents` table: region, urgency `A1`/`A2`/`B`,
`response_time_seconds`, etc.). All query logic lives in one core layer,
`seconds/queries.py`; the REST API (`seconds/api.py`) and the MCP server
(`seconds/mcp_server.py`) are thin wrappers over it — don't duplicate query logic.

## Answering data questions — use the MCP

For any question about the incidents / ambulance-dispatch data (averages, counts,
group-bys, trends, e.g. *"average A1 response time in September"*), **answer using
the `seconds` MCP tools**:

- `list_schema` — discover columns, roles, example values, available ops (call first if unsure)
- `list_column_values` — distinct values of a categorical column
- `summarize` — one aggregate (avg/sum/min/max/count) with filters
- `group_by` — aggregate grouped by a dimension or time bucket (day/week/month)
- `trend` — time series with optional moving average

**Do not** answer these by shelling out to `curl` or by starting/hitting the local
HTTP server. Filter correctly: match `urgency` and the date range the user asked
for — don't report an unfiltered whole-table average.

If the `seconds` MCP tools are not loaded (they attach at session start), restart
the session or run `/mcp` to reconnect, rather than falling back to `curl`.

## Layout

Python core (installable) at the root; the whole web UI is isolated under `web/`.

```
seconds/   core engine (queries, api, mcp_server, schema, db, stats, call_log)
seed/      sample-data generator (fresh random data each reset)
tests/     unit + API tests
data/      generated SQLite dbs (git-ignored)
web/       Reflex + buridan/ui app — rxconfig.py, dashboard/, components/, blocks/, assets/
start.sh   one-command launcher (api | web | mcp | test | setup)
```

## Common commands

`./start.sh <cmd>` handles venv + deps + seeding, or do it manually:

```bash
source .venv/bin/activate
python -m seed.generate_data          # (re)generate data/seconds.db
uvicorn seconds.api:app --reload      # REST API + docs at /docs   (./start.sh api)
cd web && reflex run                  # web dashboard at :3000     (./start.sh web)
python -m pytest -q                   # run the test suite         (./start.sh test)
```

Note: `reflex run` must be invoked from `web/` (that's where `rxconfig.py` lives).

## Conventions

- Column and aggregation **names** are validated against the whitelist in
  `seconds/schema.py` before any SQL is built; filter **values** are always bound
  parameters; query connections are read-only. Preserve this safety model when
  adding queries.
- Add new summarization capabilities in `seconds/queries.py` first, then expose
  them in both `api.py` and `mcp_server.py`.

## Web dashboard (Reflex + buridan/ui)

`web/` holds the entire Reflex app (Docs / Database / Logs); run `reflex run`
from there. `web/dashboard/` imports the `seconds` core directly, and buridan
components live in `web/components/` and `web/blocks/`. Call tracing goes to a
**separate** DB (`data/seconds_logs.db`) via `seconds/call_log.py` (the
`logged()` decorator wraps the MCP tools; a FastAPI middleware logs REST calls).

- **Backend server:** `web/.env` pins `REFLEX_USE_GRANIAN=false` so Reflex uses
  **uvicorn**. Do not remove this — granian's Rust/pyo3 layer panics
  (*"Cannot drop pointer into Python heap…"*) on state events in this version.
- Event handlers must round-trip to the backend; if the UI shows a persistent
  "Connection Error", check that only one `reflex run` owns ports 3000/8001.
