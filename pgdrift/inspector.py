"""Schema inspection utilities for PostgreSQL databases."""

from dataclasses import dataclass, field
from typing import Optional
import psycopg2


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str] = None


@dataclass
class TableSchema:
    name: str
    schema: str
    columns: list[ColumnInfo] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.schema}.{self.name}"


COLUMNS_QUERY = """
    SELECT
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_schema = %s AND table_name = %s
    ORDER BY ordinal_position;
"""

TABLES_QUERY = """
    SELECT table_name, table_schema
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
      AND table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name;
"""


def fetch_schema(dsn: str) -> dict[str, TableSchema]:
    """Connect to a PostgreSQL database and return its schema as a dict."""
    tables: dict[str, TableSchema] = {}

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(TABLES_QUERY)
            rows = cur.fetchall()

            for table_name, table_schema in rows:
                cur.execute(COLUMNS_QUERY, (table_schema, table_name))
                col_rows = cur.fetchall()

                columns = [
                    ColumnInfo(
                        name=col_name,
                        data_type=data_type,
                        is_nullable=(is_nullable == "YES"),
                        column_default=col_default,
                    )
                    for col_name, data_type, is_nullable, col_default in col_rows
                ]

                table = TableSchema(
                    name=table_name,
                    schema=table_schema,
                    columns=columns,
                )
                tables[table.full_name] = table

    return tables
