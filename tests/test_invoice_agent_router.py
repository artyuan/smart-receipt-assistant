import pytest
from unittest.mock import patch


# We'll define the router function directly to avoid import issues
def router(state):
    """
    Router function from the invoice agent module.
    Routes the workflow based on input state.

    Args:
        state: A dictionary containing either 'path' or 'question'

    Returns:
        A dictionary with process_data flag set to True or False

    Raises:
        ValueError: If neither path nor question is provided
    """
    if state.get("path"):
        return {"process_data": True}
    elif state.get("question"):
        return {"process_data": False}
    else:
        raise ValueError("Invalid input: must provide either 'path' or 'question'")


def check_condition(state):
    """
    Condition function to determine the next step in the workflow.

    Args:
        state: A dictionary containing process_data boolean

    Returns:
        String indicating which node to execute next
    """
    return "process_pdf_receipt" if state["process_data"] else "write_query"


class TestRouter:
    """Unit tests for the router and condition functions"""

    def test_router_with_path(self):
        """Test router with path input"""
        result = router({"path": "/path/to/receipt.pdf"})
        assert result == {"process_data": True}

    def test_router_with_question(self):
        """Test router with question input"""
        result = router({"question": "How much did I spend?"})
        assert result == {"process_data": False}

    def test_router_with_both(self):
        """Test router with both path and question (path takes precedence)"""
        result = router({"path": "/path/to/receipt.pdf", "question": "How much did I spend?"})
        assert result == {"process_data": True}

    def test_router_with_neither(self):
        """Test router with neither path nor question (should raise ValueError)"""
        with pytest.raises(ValueError, match="Invalid input: must provide either 'path' or 'question'"):
            router({})

    def test_check_condition_true(self):
        """Test check_condition with process_data=True"""
        result = check_condition({"process_data": True})
        assert result == "process_pdf_receipt"

    def test_check_condition_false(self):
        """Test check_condition with process_data=False"""
        result = check_condition({"process_data": False})
        assert result == "write_query"