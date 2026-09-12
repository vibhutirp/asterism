from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import snowflake_connection


def test_connect_to_snowflake_reads_required_and_default_env(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct")
    monkeypatch.setenv("SNOWFLAKE_USER", "user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "secret")
    monkeypatch.delenv("SNOWFLAKE_WAREHOUSE", raising=False)
    monkeypatch.delenv("SNOWFLAKE_DATABASE", raising=False)
    monkeypatch.delenv("SNOWFLAKE_SCHEMA", raising=False)

    connect = MagicMock()
    monkeypatch.setattr(snowflake_connection.snowflake.connector, "connect", connect)

    snowflake_connection.connect_to_snowflake()

    connect.assert_called_once_with(
        account="acct",
        user="user",
        password="secret",
        warehouse="COMPUTE_WH",
        database="WORKFORCE_ANALYTICS",
        schema="PUBLIC",
    )


def test_connect_to_snowflake_uses_optional_env(monkeypatch) -> None:
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct")
    monkeypatch.setenv("SNOWFLAKE_USER", "user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "secret")
    monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "WH")
    monkeypatch.setenv("SNOWFLAKE_DATABASE", "DB")
    monkeypatch.setenv("SNOWFLAKE_SCHEMA", "SCHEMA")

    connect = MagicMock()
    monkeypatch.setattr(snowflake_connection.snowflake.connector, "connect", connect)

    snowflake_connection.connect_to_snowflake()

    assert connect.call_args.kwargs["warehouse"] == "WH"
    assert connect.call_args.kwargs["database"] == "DB"
    assert connect.call_args.kwargs["schema"] == "SCHEMA"


def test_connect_to_snowflake_missing_required_env(monkeypatch) -> None:
    monkeypatch.delenv("SNOWFLAKE_ACCOUNT", raising=False)
    monkeypatch.setenv("SNOWFLAKE_USER", "user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "secret")

    with pytest.raises(KeyError, match="SNOWFLAKE_ACCOUNT"):
        snowflake_connection.connect_to_snowflake()


def test_main_prints_current_version(monkeypatch, capsys) -> None:
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchone.return_value = ["9.9.9"]

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value = cursor

    monkeypatch.setattr(snowflake_connection, "connect_to_snowflake", lambda: connection)

    snowflake_connection.main()

    cursor.execute.assert_called_once_with("SELECT CURRENT_VERSION()")
    assert "Connected to Snowflake. Version: 9.9.9" in capsys.readouterr().out
