"""Shared page shell: a sidebar with navigation + a content area."""

from __future__ import annotations

import reflex as rx

NAV = [
    ("Docs", "/", "book-open"),
    ("Database", "/database", "database"),
    ("Logs", "/logs", "scroll-text"),
]


def _nav_link(label: str, href: str, icon: str) -> rx.Component:
    active = rx.State.router.page.path == href
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label, class_name="text-sm font-medium"),
            spacing="3",
            align="center",
            class_name=rx.cond(
                active,
                "px-3 py-2 rounded-lg w-full bg-secondary text-foreground",
                "px-3 py-2 rounded-lg w-full text-muted-foreground hover:bg-muted hover:text-foreground",
            ),
        ),
        href=href,
        class_name="w-full no-underline",
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("ambulance", size=22, class_name="text-primary"),
                rx.heading("SECONDS", size="5", class_name="cn-font-heading"),
                spacing="2",
                align="center",
                class_name="px-2 py-1",
            ),
            rx.text(
                "Ambulance-dispatch data summary",
                class_name="px-2 text-xs text-muted-foreground",
            ),
            rx.divider(class_name="my-2"),
            *[_nav_link(label, href, icon) for label, href, icon in NAV],
            rx.spacer(),
            rx.color_mode.button(),
            spacing="1",
            align="start",
            class_name="h-full w-full p-3",
        ),
        class_name=(
            "hidden md:flex flex-col w-64 shrink-0 h-screen sticky top-0 "
            "border-r border-input bg-card"
        ),
    )


def page_shell(title: str, description: str, *content: rx.Component) -> rx.Component:
    """Wrap page content with the sidebar and a header."""
    return rx.hstack(
        sidebar(),
        rx.box(
            rx.vstack(
                rx.heading(title, size="7", class_name="cn-font-heading"),
                rx.text(description, class_name="text-muted-foreground"),
                rx.divider(class_name="my-4"),
                *content,
                spacing="4",
                align="start",
                class_name="w-full max-w-6xl mx-auto p-6 md:p-10",
            ),
            class_name="flex-1 min-h-screen bg-background",
        ),
        spacing="0",
        align="start",
        class_name="w-full bg-background",
    )
