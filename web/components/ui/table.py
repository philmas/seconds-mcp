from typing import Any, Literal

from reflex.components.component import Component, ComponentNamespace
from reflex.vars.base import Var
from reflex_components_core.core.foreach import foreach
from reflex_components_core.el import (
    Caption,
    Div,
    Table,
    Tbody,
    Td,
    Tfoot,
    Th,
    Thead,
    Tr,
)

from .core import CoreComponent, cn

LiteralAlign = Literal["left", "center", "right"]


class ClassNames:
    ROOT = "w-full overflow-auto rounded-lg border border-input bg-card shadow-sm"
    TABLE = "w-full caption-bottom text-sm border-collapse"
    HEADER = "[&_tr]:border-b bg-secondary/50 backdrop-blur-sm sticky top-0"
    BODY = "[&_tr:last-child]:border-0"
    FOOTER = "border-t bg-muted/50 font-medium [&>tr]:last:border-b-0"
    ROW = "border-b transition-colors data-[state=selected]:bg-muted hover:bg-muted/50"
    HEAD = "h-10 px-4 text-left align-middle font-semibold text-muted-foreground [&:has([role=checkbox])]:pr-0 whitespace-nowrap"
    CELL = "p-4 align-middle [&:has([role=checkbox])]:pr-0"
    CAPTION = "mt-4 text-sm text-muted-foreground"


class TableRoot(Div, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:

        cls.set_class_name(ClassNames.ROOT, props)

        table_props = {
            "class_name": ClassNames.TABLE,
        }
        return super().create(Table.create(*children, **table_props), **props)


class TableHeader(Thead, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:
        cls.set_class_name(ClassNames.HEADER, props)
        return super().create(*children, **props)


class TableBody(Tbody, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:
        cls.set_class_name(ClassNames.BODY, props)
        return super().create(*children, **props)


class TableFooter(Tfoot, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:
        cls.set_class_name(ClassNames.FOOTER, props)
        return super().create(*children, **props)


class TableRow(Tr, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:
        cls.set_class_name(ClassNames.ROW, props)
        return super().create(*children, **props)


class TableHead(Th, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:
        cls.set_class_name(ClassNames.HEAD, props)
        return super().create(*children, **props)


class TableCell(Td, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:
        cls.set_class_name(ClassNames.CELL, props)
        return super().create(*children, **props)


class TableCaption(Caption, CoreComponent):
    @classmethod
    def create(cls, *children, **props) -> Component:
        cls.set_class_name(ClassNames.CAPTION, props)
        return super().create(*children, **props)


class HighLevelTable(TableRoot):
    @classmethod
    def create(
        cls,
        data: Var[list[dict[str, Any]]] | list[dict[str, Any]],
        columns: list[dict[str, Any]] | None = None,
        striped: bool = False,
        **props,
    ) -> Component:

        if columns is None and isinstance(data, list) and len(data) > 0:
            columns = [
                {"header": k.replace("_", " ").title(), "accessor": k}
                for k in data[0].keys()
            ]
        elif columns is None:
            columns = []

        header_row = TableRow.create(
            *[
                TableHead.create(
                    col.get("header", ""),
                    class_name=cn(
                        "text-right" if col.get("align") == "right" else "",
                        "text-center" if col.get("align") == "center" else "",
                        col.get("class_name", ""),
                    ),
                )
                for col in columns
            ]
        )

        if isinstance(data, Var):
            body_content = foreach(
                data,
                lambda row: TableRow.create(
                    *[
                        TableCell.create(
                            row[col["accessor"]],
                            class_name=cn(
                                "text-right" if col.get("align") == "right" else "",
                                "text-center" if col.get("align") == "center" else "",
                                col.get("class_name", ""),
                            ),
                        )
                        for col in columns
                    ],
                    class_name=cn(
                        "even:bg-secondary/30" if striped else "",
                    ),
                ),
            )
        else:
            body_content = [
                TableRow.create(
                    *[
                        TableCell.create(
                            row.get(col["accessor"], ""),
                            class_name=cn(
                                "text-right" if col.get("align") == "right" else "",
                                "text-center" if col.get("align") == "center" else "",
                                col.get("class_name", ""),
                            ),
                        )
                        for col in columns
                    ],
                    class_name=cn(
                        "even:bg-secondary/30" if striped and i % 2 == 1 else "",
                    ),
                )
                for i, row in enumerate(data)
            ]

        return super().create(
            TableHeader.create(header_row),
            TableBody.create(
                body_content if not isinstance(body_content, Var) else body_content
            ),
            **props,
        )


class TableNamespace(ComponentNamespace):
    root = staticmethod(TableRoot.create)
    header = staticmethod(TableHeader.create)
    body = staticmethod(TableBody.create)
    footer = staticmethod(TableFooter.create)
    row = staticmethod(TableRow.create)
    head = staticmethod(TableHead.create)
    cell = staticmethod(TableCell.create)
    caption = staticmethod(TableCaption.create)
    __call__ = staticmethod(HighLevelTable.create)


table = TableNamespace()
