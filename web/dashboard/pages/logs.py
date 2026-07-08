"""Logs page: a trace of every MCP tool call and REST request."""

from __future__ import annotations

import reflex as rx

from components.ui.badge import badge
from components.ui.button import button
from components.ui.card import card

from ..layout import page_shell
from ..state import LogsState


def _source_badge(source: str) -> rx.Component:
    return badge(
        source,
        variant=rx.cond(source == "mcp", "default", "secondary"),
    )


def _status_badge(status: str) -> rx.Component:
    return badge(
        status,
        variant=rx.cond(status == "ok", "outline", "destructive"),
    )


def _log_row(row: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            row["time"],
            class_name="p-3 align-top whitespace-nowrap text-muted-foreground",
        ),
        rx.el.td(_source_badge(row["source"]), class_name="p-3 align-top"),
        rx.el.td(rx.code(row["name"]), class_name="p-3 align-top whitespace-nowrap"),
        rx.el.td(
            rx.text(row["arguments"], class_name="text-xs font-mono break-all"),
            class_name="p-3 align-top max-w-md",
        ),
        rx.el.td(_status_badge(row["status"]), class_name="p-3 align-top"),
        rx.el.td(
            row["duration"],
            class_name="p-3 align-top text-right whitespace-nowrap text-muted-foreground",
        ),
        class_name="border-b border-input hover:bg-muted/40",
    )


def _logs_table() -> rx.Component:
    return card.root(
        card.content(
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th("Time (UTC)", class_name="p-3 text-left font-semibold"),
                            rx.el.th("Source", class_name="p-3 text-left font-semibold"),
                            rx.el.th("Call", class_name="p-3 text-left font-semibold"),
                            rx.el.th("Arguments", class_name="p-3 text-left font-semibold"),
                            rx.el.th("Status", class_name="p-3 text-left font-semibold"),
                            rx.el.th("Duration", class_name="p-3 text-right font-semibold"),
                            class_name="border-b border-input bg-secondary/50 sticky top-0",
                        )
                    ),
                    rx.el.tbody(rx.foreach(LogsState.logs, _log_row)),
                    class_name="w-full text-sm border-collapse",
                ),
                class_name="w-full overflow-auto rounded-lg border border-input max-h-[70vh]",
            ),
        ),
        class_name="w-full p-0",
    )


def logs_page() -> rx.Component:
    return page_shell(
        "Logs & traces",
        "Every MCP tool call and REST request, newest first.",
        rx.hstack(
            button(
                rx.icon("refresh-cw", size=14),
                "Refresh",
                on_click=LogsState.refresh,
                variant="outline",
            ),
            button(
                rx.icon("trash-2", size=14),
                "Clear",
                on_click=LogsState.clear_logs,
                variant="ghost",
            ),
            rx.spacer(),
            rx.text(
                rx.cond(
                    LogsState.logs.length() > 0,
                    LogsState.logs.length().to_string() + " entries",
                    "No calls recorded yet",
                ),
                class_name="text-sm text-muted-foreground",
            ),
            width="100%",
            align="center",
            spacing="3",
        ),
        _logs_table(),
    )
