import pytest
import os
import sys
from unittest.mock import patch, MagicMock


# Mock OpenAI and other external dependencies for all tests
@pytest.fixture(scope="session", autouse=True)
def mock_external_dependencies():
    """Mock external dependencies that require API keys or external services"""
    # Create mocks for OpenAI and related modules
    mock_openai = MagicMock()
    mock_langchain_openai = MagicMock()
    mock_chat_models = MagicMock()

    # Apply mocks to prevent actual imports
    sys.modules['openai'] = mock_openai
    sys.modules['langchain_openai'] = mock_langchain_openai
    sys.modules['langchain_openai.chat_models'] = mock_chat_models

    # If you need to mock other external services, add them here
    yield


# This file contains pytest fixtures that can be reused across tests

@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables for testing"""
    with patch.dict(os.environ, {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "DB_NAME": "test_db"
    }):
        yield


@pytest.fixture
def mock_connection():
    """Create a mock database connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def mock_engine():
    """Create a mock SQLAlchemy engine"""
    return MagicMock()

@pytest.fixture
def mock_langgraph_checkpoint():
    """
    Mock the LangGraph MemorySaver to avoid any persistence issues in tests
    """
    with patch('langgraph.checkpoint.memory.MemorySaver') as mock:
        memory_instance = MagicMock()
        mock.return_value = memory_instance
        yield mock

@pytest.fixture
def mock_pdf_processor():
    """Mock the PDF processing function"""
    with patch('src.receipt_processing.process_pdf') as mock:
        mock.return_value = "mocked pdf content"
        yield mock

@pytest.fixture
def mock_data_extractor():
    """Mock the receipt data extraction function"""
    with patch('src.receipt_processing.extract_receipt_data') as mock:
        mock.return_value = {
            "vendor": "Test Store",
            "date": "2023-05-01",
            "amount": 42.99,
            "items": [
                {"name": "Item 1", "price": 10.99},
                {"name": "Item 2", "price": 32.00}
            ]
        }
        yield mock

@pytest.fixture
def mock_db_insertion():
    """Mock the database insertion function"""
    with patch('src.database.insert_sql_query') as mock:
        mock.return_value = None
        yield mock

@pytest.fixture
def mock_query_writer():
    """Mock the SQL query writer function"""
    with patch('src.sql_query.write_query') as mock:
        mock.return_value = "SELECT * FROM receipts WHERE vendor = 'Test Store'"
        yield mock

@pytest.fixture
def mock_query_executor():
    """Mock the SQL query executor function"""
    with patch('src.sql_query.execute_query') as mock:
        mock.return_value = [
            {
                "vendor": "Test Store",
                "date": "2023-05-01",
                "amount": 42.99
            }
        ]
        yield mock

@pytest.fixture
def mock_answer_generator():
    """Mock the answer generator function"""
    with patch('src.sql_query.generate_answer') as mock:
        mock.return_value = "The total amount spent at Test Store on 2023-05-01 was $42.99"
        yield mock