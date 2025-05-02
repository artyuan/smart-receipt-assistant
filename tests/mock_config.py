import sys
from unittest.mock import MagicMock


# Create mock modules to prevent actual imports
def setup_mock_config():
    """Set up mock config and related modules for testing"""
    # Create mock for OpenAI
    mock_openai = MagicMock()
    mock_openai.OpenAIError = type('OpenAIError', (Exception,), {})
    sys.modules['openai'] = mock_openai

    # Create mock for langchain modules
    mock_langchain_core = MagicMock()
    sys.modules['langchain_core'] = mock_langchain_core
    sys.modules['langchain_core.load'] = MagicMock()
    sys.modules['langchain_core.load.serializable'] = MagicMock()

    mock_langchain_openai = MagicMock()
    mock_chat_openai = MagicMock()
    mock_chat_models = MagicMock()

    # Set up ChatOpenAI mock
    mock_chat_openai.ChatOpenAI = MagicMock()

    # Set up module structure
    sys.modules['langchain_openai'] = mock_langchain_openai
    sys.modules['langchain_openai.chat_models'] = mock_chat_models
    sys.modules['langchain_openai.chat_models.base'] = MagicMock()

    # Create mock config with database credentials
    mock_config = MagicMock()
    mock_config.DB_HOST = 'localhost'
    mock_config.DB_PORT = '5432'
    mock_config.DB_USER = 'testuser'
    mock_config.DB_PASSWORD = 'testpass'
    mock_config.DB_NAME = 'testdb'

    # Set up llm mock to prevent actual API calls
    mock_config.llm = MagicMock()

    # Apply the mock to the sys.modules
    sys.modules['src.config'] = mock_config

    return mock_config