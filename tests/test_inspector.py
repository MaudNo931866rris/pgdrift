"""Unit tests for pgdrift.inspector using a mocked psycopg2 connection."""

from unittest.mock import MagicMock, patch, call
import pytest
from pgdrift.inspector import fetch_schema, TableSchema, ColumnInfo


TABLES_ROWS = [
    ("users", "public"),
    ("orders", "public"),
]

USERS_COLUMNS = [
    ("id", "integer", "NO", "nextval('users_id_seq'::regclass)"),
    ("email", "character varying", "NO", None),
]

ORDERS_COLUMNS = [
    ("id", "integer", "NO", None),
    ("user_id", "integer", "YES", None),
    ("total", "numeric", "NO", None),
]


@pytest.fixture
def mock_conn():
    cursor = MagicMock()
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)

    def fetchall_side_effect():
        calls = cursor.execute.call_count
        if calls == 1:
            return TABLES_ROWS
        elif calls == 2:
            return USERS_COLUMNS
        elif calls == 3:
            return ORDERS_COLUMNS
        return []

    cursor.fetchall.side_effect = fetchall_side_effect

    conn = MagicMock()
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor
    return conn


@patch("pgdrift.inspector.psycopg2.connect")
def test_fetch_schema_returns_tables(mock_connect, mock_conn):
    mock_connect.return_value = mock_conn
    schema = fetch_schema("postgresql://localhost/test")
    assert "public.users" in schema
    assert "public.orders" in schema


@patch("pgdrift.inspector.psycopg2.connect")
def test_fetch_schema_columns(mock_connect, mock_conn):
    mock_connect.return_value = mock_conn
    schema = fetch_schema("postgresql://localhost/test")
    users = schema["public.users"]
    assert len(users.columns) == 2
    assert users.columns[0].name == "id"
    assert users.columns[0].data_type == "integer"
    assert users.columns[0].is_nullable is False


@patch("pgdrift.inspector.psycopg2.connect")
def test_fetch_schema_nullable(mock_connect, mock_conn):
    mock_connect.return_value = mock_conn
    schema = fetch_schema("postgresql://localhost/test")
    orders = schema["public.orders"]
    user_id_col = next(c for c in orders.columns if c.name == "user_id")
    assert user_id_col.is_nullable is True


@patch("pgdrift.inspector.psycopg2.connect")
def test_fetch_schema_uses_dsn(mock_connect, mock_conn):
    mock_connect.return_value = mock_conn
    dsn = "postgresql://user:pass@host/db"
    fetch_schema(dsn)
    mock_connect.assert_called_once_with(dsn)
