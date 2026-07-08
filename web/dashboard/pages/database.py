"""Database page: live statistics + a reset / reinitialize control."""

from __future__ import annotations

import reflex as rx

from components.ui.badge import badge
from components.ui.button import button
from components.ui.card import card
from components.ui.metric import metric

from ..layout import page_shell
from ..state import StatsState


def _stat_cards() -> rx.Component:
    return rx.grid(
        metric("Total incidents", StatsState.total_display),
        metric("Avg response time", StatsState.avg_response_display),
        metric("Min / Max response", StatsState.min_max_display),
        metric("Transported", StatsState.pct_transported_display),
        metric("Distinct vehicles", StatsState.vehicles_display),
        metric("Date range", StatsState.date_range_display),
        columns=rx.breakpoints(initial="1", sm="2", lg="3"),
        spacing="4",
        width="100%",
    )


def _breakdown_table(title: str, dim: str, rows) -> rx.Component:
    return card.root(
        card.header(card.title(title)),
        card.content(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        rx.el.th(dim, class_name="p-2 text-left font-semibold"),
                        rx.el.th("Count", class_name="p-2 text-right font-semibold"),
                        rx.el.th(
                            "Avg response (s)",
                            class_name="p-2 text-right font-semibold",
                        ),
                        class_name="border-b border-input bg-secondary/50",
                    )
                ),
                rx.el.tbody(
                    rx.foreach(
                        rows,
                        lambda r: rx.el.tr(
                            rx.el.td(r["key"], class_name="p-2"),
                            rx.el.td(r["count"], class_name="p-2 text-right"),
                            rx.el.td(r["avg"], class_name="p-2 text-right"),
                            class_name="border-b border-input",
                        ),
                    )
                ),
                class_name="w-full text-sm border-collapse",
            ),
        ),
        class_name="w-full",
    )


def _region_chart() -> rx.Component:
    return card.root(
        card.header(
            card.title("Average response time per region"),
            card.description("Seconds — grounded in the current database."),
        ),
        card.content(
            rx.recharts.bar_chart(
                rx.recharts.cartesian_grid(
                    horizontal=True, vertical=False, class_name="opacity-30"
                ),
                rx.recharts.x_axis(
                    data_key="name",
                    tick_line=False,
                    axis_line=False,
                    custom_attrs={"fontSize": "11px"},
                ),
                rx.recharts.y_axis(
                    tick_line=False,
                    axis_line=False,
                    width=45,
                    custom_attrs={"fontSize": "11px"},
                ),
                rx.recharts.bar(
                    data_key="avg",
                    fill="var(--chart-1)",
                    is_animation_active=False,
                    max_bar_size=60,
                    radius=[4, 4, 0, 0],
                ),
                data=StatsState.region_chart,
                width="100%",
                height=260,
            ),
        ),
        class_name="w-full",
    )


def _reset_panel() -> rx.Component:
    return card.root(
        card.header(
            card.title("Reset / reinitialize database"),
            card.description(
                "Rebuild the incidents table with a fresh, random sample dataset. "
                "The statistics above recompute from it, so they stay the "
                "ground truth for validating agent / MCP answers."
            ),
        ),
        card.content(
            rx.hstack(
                button(
                    rx.cond(StatsState.resetting, "Resetting…", "Reset database"),
                    on_click=StatsState.reset_database,
                    disabled=StatsState.resetting,
                    variant="destructive",
                ),
                rx.cond(
                    StatsState.last_reset != "",
                    rx.hstack(
                        badge("last reset", variant="outline"),
                        rx.text(
                            StatsState.last_reset,
                            class_name="text-sm text-muted-foreground",
                        ),
                        align="center",
                        spacing="2",
                    ),
                ),
                align="center",
                spacing="4",
            ),
        ),
        class_name="w-full",
    )


def database_page() -> rx.Component:
    return page_shell(
        "Database",
        "Statistics computed live from the incidents database.",
        _reset_panel(),
        _stat_cards(),
        _region_chart(),
        rx.grid(
            _breakdown_table("By urgency", "Urgency", StatsState.by_urgency_rows),
            _breakdown_table("By region", "Region", StatsState.by_region_rows),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="4",
            width="100%",
        ),
    )
