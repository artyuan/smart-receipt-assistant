from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from src.receipt_processing import process_pdf, extract_receipt_data
from src.sql_query import write_query, execute_query, generate_answer
from src.database import insert_sql_query
from langgraph.checkpoint.memory import MemorySaver

class GraphState(TypedDict):
    path: str
    receipt: str
    result: str
    process_data: bool
    question: str
    query: str
    answer: str

def router(state: GraphState) -> GraphState:
    if state.get("path"):
        return {"process_data": True}
    elif state.get("question"):
        return {"process_data": False}
    else:
        raise ValueError("Invalid input: must provide either 'path' or 'question'")

def check_condition(state: GraphState) -> str:
    return "process_pdf_receipt" if state["process_data"] else "write_query"

# Node definitions
def process_pdf_node(state: GraphState) -> GraphState:
    return {"receipt": process_pdf(state["path"])}

def extract_data_node(state: GraphState) -> GraphState:
    return {"result": extract_receipt_data(state["receipt"])}

def insert_data_node(state: GraphState) -> GraphState:
    insert_sql_query(state["result"])
    return {}

def write_query_node(state: GraphState) -> GraphState:
    return {"query": write_query(state["question"])}

def execute_query_node(state: GraphState) -> GraphState:
    return {"result": execute_query(state["query"])}

def generate_answer_node(state: GraphState) -> GraphState:
    return {"answer": generate_answer(state["question"], state["query"], state["result"])}

def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("router", router)
    workflow.add_node("process_pdf_receipt", process_pdf_node)
    workflow.add_node("extract_data", extract_data_node)
    workflow.add_node("insert_data", insert_data_node)
    workflow.add_node("write_query", write_query_node)
    workflow.add_node("execute_query", execute_query_node)
    workflow.add_node("generate_answer", generate_answer_node)

    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", check_condition)
    workflow.add_edge("process_pdf_receipt", "extract_data")
    workflow.add_edge("extract_data", "insert_data")
    workflow.add_edge("insert_data", END)
    workflow.add_edge("write_query", "execute_query")
    workflow.add_edge("execute_query", "generate_answer")
    workflow.add_edge("generate_answer", END)
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)