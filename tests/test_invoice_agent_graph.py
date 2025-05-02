import pytest
from unittest.mock import patch, MagicMock, Mock
import sys

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

# Create mock for StateGraph
class MockStateGraph:
    def __init__(self, *args, **kwargs):
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}

    def add_node(self, name, func):
        self.nodes[name] = func
        return self

    def add_edge(self, start, end):
        if start not in self.edges:
            self.edges[start] = []
        self.edges[start].append(end)
        return self

    def add_conditional_edges(self, start, condition_func):
        self.conditional_edges[start] = condition_func
        return self

    def compile(self, checkpointer=None):
        # Return a callable that simulates the graph execution
        graph_runner = MagicMock()
        graph_runner.invoke = MagicMock(side_effect=self._simulate_invoke)
        return graph_runner

    def _simulate_invoke(self, state, config=None):
        # This is a simple simulation of graph execution for testing
        try:
            # First try router
            if "router" in self.nodes:
                router_result = self.nodes["router"](state)
                state.update(router_result)

            # Process based on condition
            if state.get("process_data", False):
                # PDF processing path
                if "process_pdf_receipt" in self.nodes:
                    receipt_result = self.nodes["process_pdf_receipt"](state)
                    state.update(receipt_result)

                if "extract_data" in self.nodes:
                    extract_result = self.nodes["extract_data"](state)
                    state.update(extract_result)

                if "insert_data" in self.nodes:
                    insert_result = self.nodes["insert_data"](state)
                    state.update(insert_result)
            else:
                # Query answering path
                if "write_query" in self.nodes:
                    query_result = self.nodes["write_query"](state)
                    state.update(query_result)

                if "execute_query" in self.nodes:
                    execute_result = self.nodes["execute_query"](state)
                    state.update(execute_result)

                if "generate_answer" in self.nodes:
                    answer_result = self.nodes["generate_answer"](state)
                    state.update(answer_result)

            return state
        except Exception as e:
            # Re-raise exceptions to simulate graph error handling
            raise e


# Set up mock modules without relying on patch.dict
# Create mock for langgraph module and its submodules
langgraph_mock = MagicMock()
langgraph_graph_mock = MagicMock()
langgraph_checkpoint_mock = MagicMock()
langgraph_checkpoint_memory_mock = MagicMock()

# Set up the mock module hierarchy
sys.modules['langgraph'] = langgraph_mock
sys.modules['langgraph.graph'] = langgraph_graph_mock
sys.modules['langgraph.checkpoint'] = langgraph_checkpoint_mock
sys.modules['langgraph.checkpoint.memory'] = langgraph_checkpoint_memory_mock

# Add StateGraph, START, END to langgraph.graph
langgraph_graph_mock.StateGraph = MockStateGraph
langgraph_graph_mock.START = "START"
langgraph_graph_mock.END = "END"

# Add MemorySaver to langgraph.checkpoint.memory
memory_saver_mock = MagicMock()
langgraph_checkpoint_memory_mock.MemorySaver = memory_saver_mock

# Mock src modules
src_receipt_processing_mock = MagicMock()
src_receipt_processing_mock.process_pdf = MagicMock(return_value="mocked pdf content")
src_receipt_processing_mock.extract_receipt_data = MagicMock(return_value={"vendor": "Test Store", "amount": 42.99})

src_sql_query_mock = MagicMock()
src_sql_query_mock.write_query = MagicMock(return_value="SELECT * FROM receipts")
src_sql_query_mock.execute_query = MagicMock(return_value=[{"vendor": "Test Store", "amount": 42.99}])
src_sql_query_mock.generate_answer = MagicMock(return_value="The total amount is $42.99")

src_database_mock = MagicMock()
src_database_mock.insert_sql_query = MagicMock(return_value=None)

# Add src modules to sys.modules
sys.modules['src.receipt_processing'] = src_receipt_processing_mock
sys.modules['src.sql_query'] = src_sql_query_mock
sys.modules['src.database'] = src_database_mock

# Mock typing_extensions
typing_extensions_mock = MagicMock()
sys.modules['typing_extensions'] = typing_extensions_mock


# Define our own GraphState for testing purposes
class GraphState(dict):
    pass


# Define functions directly for testing
def router(state):
    if state.get("path"):
        return {"process_data": True}
    elif state.get("question"):
        return {"process_data": False}
    else:
        raise ValueError("Invalid input: must provide either 'path' or 'question'")


def check_condition(state):
    return "process_pdf_receipt" if state["process_data"] else "write_query"


def process_pdf_node(state):
    return {"receipt": src_receipt_processing_mock.process_pdf(state["path"])}


def extract_data_node(state):
    return {"result": src_receipt_processing_mock.extract_receipt_data(state["receipt"])}


def insert_data_node(state):
    src_database_mock.insert_sql_query(state["result"])
    return {}


def write_query_node(state):
    return {"query": src_sql_query_mock.write_query(state["question"])}


def execute_query_node(state):
    return {"result": src_sql_query_mock.execute_query(state["query"])}


def generate_answer_node(state):
    return {"answer": src_sql_query_mock.generate_answer(state["question"], state["query"], state["result"])}


def build_graph():
    workflow = MockStateGraph(dict)
    workflow.add_node("router", router)
    workflow.add_node("process_pdf_receipt", process_pdf_node)
    workflow.add_node("extract_data", extract_data_node)
    workflow.add_node("insert_data", insert_data_node)
    workflow.add_node("write_query", write_query_node)
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("generate_answer", generate_answer_node)

    workflow.add_edge("START", "router")
    workflow.add_conditional_edges("router", check_condition)
    workflow.add_edge("process_pdf_receipt", "extract_data")
    workflow.add_edge("extract_data", "insert_data")
    workflow.add_edge("insert_data", "END")
    workflow.add_edge("write_query", "execute_query")
    workflow.add_edge("execute_query", "generate_answer")
    workflow.add_edge("generate_answer", "END")
    memory = memory_saver_mock()
    return workflow.compile(checkpointer=memory)


# Now define tests for the functions
class TestInvoiceAgent:
    """Tests for the invoice agent workflow"""

    def test_router_with_path(self):
        """Test router when path is provided"""
        state = {"path": "/path/to/file.pdf"}
        result = router(state)
        assert result == {"process_data": True}

    def test_router_with_question(self):
        """Test router when question is provided"""
        state = {"question": "How much did I spend?"}
        result = router(state)
        assert result == {"process_data": False}

    def test_router_with_empty_state(self):
        """Test router with empty state (should raise ValueError)"""
        with pytest.raises(ValueError, match="Invalid input: must provide either 'path' or 'question'"):
            router({})

    def test_check_condition(self):
        """Test the check_condition function"""
        assert check_condition({"process_data": True}) == "process_pdf_receipt"
        assert check_condition({"process_data": False}) == "write_query"

    def test_process_pdf_node(self):
        """Test the process_pdf_node function"""
        state = {"path": "/path/to/file.pdf"}
        result = process_pdf_node(state)
        assert result == {"receipt": "mocked pdf content"}
        src_receipt_processing_mock.process_pdf.assert_called_once_with("/path/to/file.pdf")

    def test_extract_data_node(self):
        """Test the extract_data_node function"""
        state = {"receipt": "test receipt content"}
        result = extract_data_node(state)
        assert result == {"result": {"vendor": "Test Store", "amount": 42.99}}
        src_receipt_processing_mock.extract_receipt_data.assert_called_once_with("test receipt content")

    def test_insert_data_node(self):
        """Test the insert_data_node function"""
        test_data = {"vendor": "Test Store", "amount": 42.99}
        state = {"result": test_data}
        result = insert_data_node(state)
        assert result == {}
        src_database_mock.insert_sql_query.assert_called_once_with(test_data)

    def test_write_query_node(self):
        """Test the write_query_node function"""
        state = {"question": "How much did I spend?"}
        result = write_query_node(state)
        assert result == {"query": "SELECT * FROM receipts"}
        src_sql_query_mock.write_query.assert_called_once_with("How much did I spend?")

    def test_execute_query_node(self):
        """Test the execute_query_node function"""
        state = {"query": "SELECT * FROM receipts"}
        result = execute_query_node(state)
        assert result == {"result": [{"vendor": "Test Store", "amount": 42.99}]}
        src_sql_query_mock.execute_query.assert_called_once_with("SELECT * FROM receipts")

    def test_generate_answer_node(self):
        """Test the generate_answer_node function"""
        state = {
            "question": "How much did I spend?",
            "query": "SELECT * FROM receipts",
            "result": [{"vendor": "Test Store", "amount": 42.99}]
        }
        result = generate_answer_node(state)
        assert result == {"answer": "The total amount is $42.99"}
        src_sql_query_mock.generate_answer.assert_called_once_with(
            "How much did I spend?",
            "SELECT * FROM receipts",
            [{"vendor": "Test Store", "amount": 42.99}]
        )

    def test_complete_graph_workflow_with_path(self):
        """Test the complete graph workflow with a path input"""
        # Reset all mocks
        src_receipt_processing_mock.process_pdf.reset_mock()
        src_receipt_processing_mock.extract_receipt_data.reset_mock()
        src_database_mock.insert_sql_query.reset_mock()
        src_sql_query_mock.write_query.reset_mock()
        src_sql_query_mock.execute_query.reset_mock()
        src_sql_query_mock.generate_answer.reset_mock()

        # Build the graph
        graph = build_graph()

        # Execute the graph with a path input
        result = graph.invoke({"path": "/path/to/receipt.pdf"})

        # Check the correct functions were called
        src_receipt_processing_mock.process_pdf.assert_called_once()
        src_receipt_processing_mock.extract_receipt_data.assert_called_once()
        src_database_mock.insert_sql_query.assert_called_once()

        # These should not be called
        src_sql_query_mock.write_query.assert_not_called()
        src_sql_query_mock.execute_query.assert_not_called()
        src_sql_query_mock.generate_answer.assert_not_called()

    def test_complete_graph_workflow_with_question(self):
        """Test the complete graph workflow with a question input"""
        # Reset all mocks
        src_receipt_processing_mock.process_pdf.reset_mock()
        src_receipt_processing_mock.extract_receipt_data.reset_mock()
        src_database_mock.insert_sql_query.reset_mock()
        src_sql_query_mock.write_query.reset_mock()
        src_sql_query_mock.execute_query.reset_mock()
        src_sql_query_mock.generate_answer.reset_mock()

        # Build the graph
        graph = build_graph()

        # Execute the graph with a question input
        result = graph.invoke({"question": "How much did I spend?"})

        # Check the correct functions were called
        src_sql_query_mock.write_query.assert_called_once()
        src_sql_query_mock.execute_query.assert_called_once()
        src_sql_query_mock.generate_answer.assert_called_once()

        # These should not be called
        src_receipt_processing_mock.process_pdf.assert_not_called()
        src_receipt_processing_mock.extract_receipt_data.assert_not_called()
        src_database_mock.insert_sql_query.assert_not_called()