"""SECONDS dashboard — a Reflex + buridan/ui interface over the summary API.

Three pages:
* ``/``          — Docs (installation, features, how-to, schema).
* ``/database``  — live statistics + reset / reinitialize.
* ``/logs``      — trace of every MCP / REST call.
"""

from __future__ import annotations

import reflex as rx

from .pages.database import database_page
from .pages.docs import docs_page
from .pages.logs import logs_page
from .state import LogsState, StatsState

# Theming comes from buridan's globals.css (Tailwind, darkMode="class"); the
# color-mode button toggles light/dark.
app = rx.App(stylesheets=["globals.css"])

app.add_page(docs_page, route="/", title="SECONDS · Docs")
app.add_page(
    database_page,
    route="/database",
    title="SECONDS · Database",
    on_load=StatsState.load,
)
app.add_page(
    logs_page,
    route="/logs",
    title="SECONDS · Logs",
    on_load=LogsState.load,
)
