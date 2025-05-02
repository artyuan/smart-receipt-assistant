import pytest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import psycopg2
from psycopg2 import sql, OperationalError, DatabaseError
from sqlalchemy.engine.base import Engine
import sys
from importlib import import_module

# Mock OpenAI and config dependencies before importing our module
# This prevents the OpenAI client from being initialized during import
sys.modules['openai'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()
sys.modules['langchain_openai.chat_models'] = MagicMock()
sys.modules['src.config'] = MagicMock()
sys.modules['src.config'].DB_HOST = 'localhost'
sys.modules['src.config'].DB_PORT = '5432'
sys.modules['src.config'].DB_USER = 'testuser'
sys.modules['src.config'].DB_PASSWORD = 'testpass'
sys.modules['src.config'].DB_NAME = 'testdb'

# Now import the functions to test
# Note: Adjusted import path to match your actual module name (database instead of database)
from src.database import (
    create_postgres_database,
    execute_sql,
    run_sql_commands,
    get_database_url,
    get_sql_database,
    insert_sql_query,
    create_db_engine,
    load_invoice_data
)


# Test create_postgres_database
@patch('src.database.psycopg2.connect')
def test_create_postgres_database_success(mock_connect):
    # Setup mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Call the function
    create_postgres_database('test_db', 'localhost', '5432', 'user', 'pass')

    # Verify the function behavior
    mock_connect.assert_called_once_with(
        dbname='postgres', user='user', password='pass', host='localhost', port='5432'
    )
    mock_conn.set_isolation_level.assert_called_once()
    assert mock_cursor.execute.call_count == 2  # DROP and CREATE commands
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch('src.database.psycopg2.connect')
def test_create_postgres_database_drop_error(mock_connect):
    # Setup mock connection and cursor with error on DROP
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = [psycopg2.Error("Drop error"), None]

    # Call the function
    create_postgres_database('test_db', 'localhost', '5432', 'user', 'pass')

    # Verify early return after error
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()
    assert mock_cursor.execute.call_count == 1  # Only the DROP command was attempted


@patch('src.database.psycopg2.connect')
def test_create_postgres_database_create_error(mock_connect):
    # Setup mock connection and cursor with error on CREATE
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = [None, psycopg2.Error("Create error")]

    # Call the function
    create_postgres_database('test_db', 'localhost', '5432', 'user', 'pass')

    # Verify both commands attempted but second failed
    assert mock_cursor.execute.call_count == 2
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


# Test execute_sql
def test_execute_sql_success():
    # Setup mock connection
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Call the function
    execute_sql(mock_conn, "SELECT * FROM test")

    # Verify behavior
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT * FROM test")
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_execute_sql_error():
    # Setup mock connection with error
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = psycopg2.Error("SQL error")

    # Call the function
    execute_sql(mock_conn, "BAD SQL")

    # Verify error handling
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_not_called()  # Should not commit on error
    mock_cursor.close.assert_called_once()  # Should still close cursor


# Test run_sql_commands
@patch('src.database.psycopg2.connect')
def test_run_sql_commands_success(mock_connect):
    # Setup mock connection
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    # Call the function with multiple commands
    commands = ["SELECT 1", "SELECT 2"]
    run_sql_commands('test_db', 'localhost', '5432', 'user', 'pass', commands)

    # Verify behavior
    mock_connect.assert_called_once()
    assert mock_conn.cursor.call_count == 2  # One cursor per command
    mock_conn.close.assert_called_once()


@patch('src.database.psycopg2.connect')
def test_run_sql_commands_connection_error(mock_connect):
    # Setup connection error
    mock_connect.side_effect = OperationalError("Connection failed")

    # Call the function
    commands = ["SELECT 1"]
    run_sql_commands('test_db', 'localhost', '5432', 'user', 'pass', commands)

    # No assertions needed - just verifying it doesn't crash
    # In a real-world scenario, you might want to verify logging behavior


@patch('src.database.psycopg2.connect')
def test_run_sql_commands_sql_error(mock_connect):
    # Setup mock connection with SQL error
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = DatabaseError("SQL syntax error")

    # Call the function
    commands = ["BAD SQL"]
    run_sql_commands('test_db', 'localhost', '5432', 'user', 'pass', commands)

    # Verify connection still closed
    mock_conn.close.assert_called_once()


# Test get_database_url
@patch('src.database.DB_USER', 'testuser')
@patch('src.database.DB_PASSWORD', 'testpass')
@patch('src.database.DB_HOST', 'testhost')
@patch('src.database.DB_PORT', '5432')
@patch('src.database.DB_NAME', 'testdb')
def test_get_database_url():
    url = get_database_url()
    assert url == "postgresql://testuser:testpass@testhost:5432/testdb"


# Test get_sql_database
@patch('src.database.get_database_url')
@patch('src.database.SQLDatabase.from_uri')
def test_get_sql_database(mock_from_uri, mock_get_url):
    # Setup mocks
    mock_get_url.return_value = "mock://connection/string"
    mock_db = MagicMock()
    mock_from_uri.return_value = mock_db

    # Call function
    result = get_sql_database()

    # Verify
    mock_get_url.assert_called_once()
    mock_from_uri.assert_called_once_with("mock://connection/string")
    assert result == mock_db


# Test insert_sql_query
@patch('src.database.run_sql_commands')
def test_insert_sql_query_success(mock_run_sql):
    # Call function
    insert_sql_query("INSERT INTO test VALUES (1, 2, 3)")

    # Verify
    mock_run_sql.assert_called_once()
    # Check the query is passed as a list with one element
    assert isinstance(mock_run_sql.call_args[0][5], list)
    assert len(mock_run_sql.call_args[0][5]) == 1
    assert mock_run_sql.call_args[0][5][0] == "INSERT INTO test VALUES (1, 2, 3)"


@patch('src.database.run_sql_commands')
def test_insert_sql_query_error(mock_run_sql):
    # Setup error
    mock_run_sql.side_effect = Exception("Database error")

    # Call function and check for exception
    with pytest.raises(Exception):
        insert_sql_query("BAD SQL")


# Test create_db_engine
@patch('src.database.create_engine')
def test_create_db_engine_success(mock_create_engine):
    # Setup mock
    mock_engine = MagicMock(spec=Engine)
    mock_create_engine.return_value = mock_engine

    # Call function
    result = create_db_engine()

    # Verify
    mock_create_engine.assert_called_once()
    assert result == mock_engine


@patch('src.database.create_engine')
def test_create_db_engine_error(mock_create_engine):
    # Setup error
    mock_create_engine.side_effect = Exception("Engine creation failed")

    # Call function and check for exception
    with pytest.raises(ConnectionError):
        create_db_engine()


# Test load_invoice_data
def test_load_invoice_data_success():
    # Setup mock engine and data
    mock_engine = MagicMock()
    test_data = {
        'id': [1, 2, 3],
        'amount': [100, 200, 300],
        'datetime': ['2023-01-01', '2023-01-02', '2023-01-03']
    }
    mock_df = pd.DataFrame(test_data)

    # Mock pandas read_sql
    with patch('src.database.pd.read_sql', return_value=mock_df):
        result = load_invoice_data(mock_engine)

    # Verify results
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert 'datetime' in result.columns
    # Verify datetime conversion
    assert pd.api.types.is_datetime64_dtype(result['datetime'])

def test_load_invoice_data_error():
    # Setup mock engine
    mock_engine = MagicMock()

    # Mock pandas read_sql with error
    with patch('src.database.pd.read_sql', side_effect=Exception("SQL error")):
        with pytest.raises(RuntimeError):
            load_invoice_data(mock_engine)