from __future__ import annotations

import runpy
import warnings
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


def test_real_snowflake_connection_when_enabled() -> None:
    import os

    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
    if os.getenv("RUN_SNOWFLAKE_E2E") != "1":
        pytest.skip("Set RUN_SNOWFLAKE_E2E=1 to run the real Snowflake E2E test.")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        pytest.skip(f"Missing Snowflake credentials: {', '.join(missing)}")

    with snowflake_connection.connect_to_snowflake() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]

    assert isinstance(version, str)
    assert version


def test_snowflake_script_executes_as_main(monkeypatch, capsys) -> None:
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.fetchone.return_value = ["10.0.0"]

    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.cursor.return_value = cursor

    connect = MagicMock(return_value=connection)
    monkeypatch.setattr(snowflake_connection.snowflake.connector, "connect", connect)
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct")
    monkeypatch.setenv("SNOWFLAKE_USER", "user")
    monkeypatch.setenv("SNOWFLAKE_PASSWORD", "secret")

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*found in sys.modules.*", category=RuntimeWarning)
        runpy.run_module("snowflake_connection", run_name="__main__")

    cursor.execute.assert_called_once_with("SELECT CURRENT_VERSION()")
    assert "Connected to Snowflake. Version: 10.0.0" in capsys.readouterr().out
