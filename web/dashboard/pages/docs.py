"""Docs page: installation, features, how-to, and a live schema explanation."""

from __future__ import annotations

import reflex as rx

from components.ui.badge import badge
from components.ui.card import card
from seconds import schema

from ..layout import page_shell

INSTALL_MD = """
## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Generate the sample database (data/seconds.db)
python -m seed.generate_data
```

Run the pieces:

```bash
uvicorn seconds.api:app --reload    # REST API + docs at /docs
python -m dashboard.dashboard        # this dashboard (via `reflex run`)
python -m seconds.mcp_server         # MCP server (stdio) for the AI agent
```
"""

FEATURES_MD = """
## Features

- **Schema discovery** — list columns, roles and example values.
- **Aggregations** — `avg`, `sum`, `min`, `max`, `count` with date-range and
  categorical filters.
- **Group-by** — aggregate by a dimension (region, urgency, vehicle) or a time
  bucket (day / week / month).
- **Trends** — time series with an optional moving average.
- **Two front doors** — a REST API *and* an MCP server, both thin wrappers over
  one core query layer (`seconds/queries.py`).
- **Grounded dashboard** — statistics computed live from the database, a one-click
  **reset** that regenerates a fresh dataset, and a **trace log** of every
  MCP / REST call.
"""

HOWTO_MD = """
## How to use

### Ask the AI agent (MCP)

Register the MCP server, then ask questions in plain language:

```bash
claude mcp add seconds -- "$(pwd)/.venv/bin/python" -m seconds.mcp_server
```

> *"What was the average A1 response time in September, and how does it compare
> per region?"*

The agent calls `list_schema`, then `summarize` / `group_by` with the right
column and filters. Every call shows up on the **Logs** page.

### Or call the REST API directly

```bash
curl -X POST localhost:8000/summarize -H 'Content-Type: application/json' -d '{
  "metric": "avg", "column": "response_time_seconds",
  "filters": {"urgency": "A1", "date_from": "2025-09-01", "date_to": "2025-09-30"}
}'
```

### Validating answers

The **Database** page shows statistics computed live from the current data, so
they are always the ground truth for the agent's answers. Hit *Reset /
reinitialize* to generate a fresh dataset — the statistics update along with it.
"""

ROLE_VARIANT = {
    "numeric": "default",
    "categorical": "secondary",
    "temporal": "outline",
}


def _schema_row(name: str, meta: dict) -> rx.Component:
    role = meta["role"]
    return rx.el.tr(
        rx.el.td(rx.code(name), class_name="p-3 align-middle"),
        rx.el.td(meta["type"], class_name="p-3 align-middle text-muted-foreground"),
        rx.el.td(
            badge(role, variant=ROLE_VARIANT.get(role, "outline"))
            if role
            else rx.text("—", class_name="text-muted-foreground"),
            class_name="p-3 align-middle",
        ),
        class_name="border-b border-input",
    )


def _schema_table() -> rx.Component:
    return card.root(
        card.header(
            card.title("Schema — the `incidents` table"),
            card.description(
                "Every query is validated against this whitelist before any SQL "
                "is built. Rendered live from seconds/schema.py."
            ),
        ),
        card.content(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th("Column", class_name="p-3 text-left font-semibold"),
                            rx.el.th("Type", class_name="p-3 text-left font-semibold"),
                            rx.el.th("Role", class_name="p-3 text-left font-semibold"),
                            class_name="border-b border-input bg-secondary/50",
                        )
                    ),
                    rx.el.tbody(
                        *[
                            _schema_row(name, meta)
                            for name, meta in schema.COLUMNS.items()
                        ]
                    ),
                    class_name="w-full text-sm border-collapse",
                ),
                class_name="w-full overflow-auto rounded-lg border border-input",
            ),
        ),
        class_name="w-full",
    )


def docs_page() -> rx.Component:
    return page_shell(
        "Documentation",
        "A simple API + MCP server that summarizes ambulance-dispatch data.",
        rx.markdown(INSTALL_MD, class_name="w-full"),
        rx.markdown(FEATURES_MD, class_name="w-full"),
        _schema_table(),
        rx.markdown(HOWTO_MD, class_name="w-full"),
    )
