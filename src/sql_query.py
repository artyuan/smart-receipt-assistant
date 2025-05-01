from langchain import hub
from src.config import llm
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from src.postgres_sql import get_sql_database
from pydantic import BaseModel

class QueryOutput(BaseModel):
    query: str

db = get_sql_database()
query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

def write_query(question: str) -> str:
    """Generate SQL query for a given user question."""
    prompt = query_prompt_template.invoke({
        "dialect": db.dialect,
        "top_k": 10,
        "table_info": db.get_table_info(),
        "input": question
    })
    structured_llm = llm.with_structured_output(QueryOutput)
    result = structured_llm.invoke(prompt)
    return result.query

def execute_query(query: str) -> str:
    tool = QuerySQLDatabaseTool(db=db)
    return tool.invoke(query)

def generate_answer(question: str, query: str, result: str) -> str:
    prompt = (
        f"Question: {question}\n"
        f"SQL Query: {query}\n"
        f"SQL Result: {result}\n"
        "If result has >2 rows, return as markdown table, else return plain text."
    )
    return llm.invoke(prompt).content