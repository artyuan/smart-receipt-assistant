import sqlalchemy
import re
import openai
import datetime
import pandas as pd
from src.config import OPENAI_API_KEY, MODEL


class SQLAgent:
    def __init__(self, db_url, schema_description, agent_state, max_iterations=2):
        self.engine = sqlalchemy.create_engine(db_url)
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.model = MODEL
        self.schema_description = schema_description
        self.max_iterations = max_iterations
        self.error_history = []
        self.agent_state = agent_state

    def _generate_sql(self, user_query, **kwargs):
        """
        Use OpenAI API to generate SQL from a natural language query.
        """
        # openai.api_key = self.openai_api_key
        msgs = []
        system_prompt = (
            """
            You are a SQL expert tasked with generating syntactically correct and semantically accurate SQL queries in response to user questions.

            You will be provided with a database schema. Carefully examine the table and column names to ensure your queries are aligned with the structure and data types.

            Your objectives:
            - Generate the most relevant SQL query (or queries) that can retrieve the information needed to answer the user question.
            - If the question requires data summarization (e.g., totals, averages, comparisons), use SQL aggregation functions (SUM, AVG, GROUP BY, etc.) as needed.
            - If the question implies time-based filtering or comparison, use the `datetime` column appropriately (e.g., using WHERE, BETWEEN, EXTRACT(YEAR FROM ...), etc.).
            - Only use columns that exist in the schema. Avoid making assumptions.
            - In cases where the question cannot be answered directly by SQL (e.g., plotting, forecasting), your goal is to write a query that retrieves the most useful raw or preprocessed data to enable that task downstream.

            Output your response as a single SQL query unless multiple queries are absolutely required.
            Do not explain the SQL—only return the raw SQL query.
            """
        )
        system_prompt = system_prompt + "\n" + f"Today's date is {datetime.date.today()}"
        msgs.append({"role": "system", "content": system_prompt})

        # Construct the prompt with schema, user query, and error history
        prompt = f"Here is the database schema:\n{self.schema_description}\n\n"
        if self.error_history:
            prompt += f"Earlier, the following SQL query was generated:\n{self.error_history[-1]['sql_query']}\n"
            prompt += f"It caused the following error:\n{self.error_history[-1]['error_message']}\n"
            prompt += "Please correct the SQL query accordingly.\n\n"

        prompt += f"Convert the following natural language query to SQL:\n'{user_query}'"
        msgs.append({"role": "user", "content": prompt})
        try:
            chat_completion = self.client.chat.completions.create(model=self.model, messages=msgs, **kwargs)
            generated_text = chat_completion.choices[0].message.content
            print(f"generated_text:\n{generated_text}")

            pattern = r"```sql\s*(.*?)\s*```"
            match = re.search(pattern, generated_text, re.DOTALL)

            if match:
                sql_query = match.group(1)
            else:
                # If the pattern is not found, assume the entire text is the SQL code
                sql_query = generated_text.strip()

            print(f"sql_query after filtering:\n{sql_query}")
            return sql_query
        except Exception as e:
            self.error_history.append({"sql_query": None, "error_message": f"OpenAI API error: {e}"})
            return None
    def _execute_sql(self, sql_query):
        """
        Execute the SQL query using SQLAlchemy and return the results as a DataFrame.
        """
        try:
            with self.engine.connect() as connection:
                df = pd.read_sql(sql_query, connection)
            return df, None
        except Exception as e:
            return None, str(e)
    def query(self):
        """
        Convert natural language query to SQL, execute it, and return the results as a DataFrame.
        """
        user_query = self.agent_state["query_for_agent"]
        for _ in range(self.max_iterations):
            sql_query = self._generate_sql(user_query)
            if sql_query:
                df, error = self._execute_sql(sql_query)
                if df is not None:
                    # if user_query not in self.agent_state["sql_results"]:
                    #     self.agent_state["sql_results"][user_query] = []
                    # self.agent_state["sql_results"][user_query].append(user_query)
                    return {"sql_results": {f"{user_query}": df}}
                else:
                    # Append the error and the generated SQL to the history for correction
                    self.error_history.append({"sql_query": sql_query, "error_message": error})
                    # append_sql_errors(self.state, error)
                    user_query += f"\nNote: The following error occurred while executing the SQL: {error}"
            else:
                self.error_history.append({"sql_query": None, "error_message": "No SQL query generated."})
                # append_sql_errors(self.state, "No SQL query generated.")

                break

        # If the loop completes without a successful query, raise an error
        return {
            "sql_error": f"Failed to generate a correct SQL query after {self.max_iterations} iterations.\nErrors: {self.error_history}"}