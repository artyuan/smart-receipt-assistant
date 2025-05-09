from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any
import sqlalchemy
import functools
from agents.sql_agent import SQLAgent
from agents.supervisor_agent import SupervisorPlanner
from agents.report_writer_agent import ReportWriterAgent
from src.config import DATABASE_URL

class GraphState(TypedDict):
    user_query: str
    plan: str
    user_query_error: str
    next_agent: str
    query_for_agent: str
    plan_errors: str
    sql_results: Dict[str, Any]
    report_errors: str
    full_report: str
    info: str

def get_schema(db_url):
    engine = sqlalchemy.create_engine(db_url)
    inspector = sqlalchemy.inspect(engine)
    schema = {}
    for table in inspector.get_table_names():
        schema[table] = [
            {"name": col["name"], "type": str(col["type"])}
            for col in inspector.get_columns(table)
        ]
    return schema

def create_sql_agent(state: GraphState, db_url)-> GraphState:
    schema_description = get_schema(db_url)
    agent = SQLAgent(db_url, schema_description, state)
    result = agent.query()
    return result


def report_writer_node(state: GraphState) -> GraphState:
    agent = ReportWriterAgent(state)
    result = agent.generate_report()
    return result


def supervisor_node(state: GraphState) -> GraphState:
    agent = SupervisorPlanner(state)
    result = agent.generate_plan()
    return result
def should_continue(state):
    if state["next_agent"] == "SQLAgent":
        return "SQLAgent"
    if state["next_agent"] == "ReportWriterAgent":
        return "ReportWriter"
    if state["next_agent"] == "FINISH":
        return END
    if state["full_report"]:
        return END

sql_agent_node = functools.partial(create_sql_agent, db_url=DATABASE_URL)

def build_report_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("SQLAgent", sql_agent_node)
    workflow.add_node("ReportWriter", report_writer_node)

    for worker_agent in ["SQLAgent", "ReportWriter"]:
        workflow.add_edge(worker_agent, "Supervisor")

    conditional_map = {k: k for k in ["SQLAgent", "ReportWriter"]}
    conditional_map[END] = END
    workflow.add_conditional_edges("Supervisor", should_continue, conditional_map)

    workflow.set_entry_point("Supervisor")
    return workflow.compile()


