import json
import re
import openai
from src.config import OPENAI_API_KEY, MODEL

class SupervisorPlanner:
    def __init__(self, state, max_iterations=2):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.model = MODEL
        self.state = state
        self.max_iterations = max_iterations
        self.error_history = []

    def _prepare_information_retrieved(self) -> str:
        """
        Formats the information retrieved so far from the AgentState into a readable string.
        """
        # info = ""
        if "info" not in self.state:
            self.state["info"] = ""
        info = self.state["info"]

        if self.state.get("sql_results"):
            info += "SQL Results:\n"
            for query, results in self.state["sql_results"].items():
                info += f"Query: {query}\n"
                #   for i, df in enumerate(results, 1):
                # info += f"Result {i}:\n{df.to_string(index=False)}\n\n"
                info += f"Result:\n{results}\n\n"

        if self.state.get("full_report"):
            info += "Report generated:\n"
            full_report = self.state.get("full_report")
            info += f"{full_report}\n\n"

        if not info:
            info = "No information retrieved yet."

        return info

    def generate_plan(self) -> dict:
        """
        Use OpenAI API to generate a plan based on the user's query, retrying up to max_iterations.
        """
        user_query = self.state["user_query"]
        if user_query:
            for iteration in range(self.max_iterations):
                msgs = []
                # Prepare the information retrieved so far
                information_retrieved = self._prepare_information_retrieved()

                if "full_report" not in self.state:
                    self.state["full_report"] = "No report generated so far"
                report = self.state["full_report"]

                # System prompt
                system_prompt = (
                    """
                    You are a highly skilled data analyst and report planner. Your task is to plan the step-by-step 
                    process for generating a comprehensive financial report based on the user's query regarding 
                    supermarket spending.

                    You have two agents at your disposal:
                    - SQLAgent: retrieves data by generating and executing SQL queries based on natural language questions.
                    - ReportWriterAgent: generates natural language summaries or report sections using the results retrieved by SQLAgent.

                    Your responsibilities:
                    - Review the current retrieval history (previous results). If none exist, begin from scratch.
                    - Break down the user’s request into clear steps needed to create the final report.
                    - At each step, determine:
                        - The next best **agent** to call (`SQLAgent` or `ReportWriterAgent`)
                        - The next **question** to pass to that agent (in natural language)
                        - A brief **plan** explaining your reasoning for the chosen step

                    Your output must be a **JSON object** with exactly the following keys:
                    - `plan`: A brief description of your current reasoning and goal
                    - `next_agent`: One of `SQLAgent`, `ReportWriterAgent`, or `FINISH`
                    - `query_for_agent`: A natural language query tailored for the selected agent

                    After all questions are fully answered and the entire report is written, set `next_agent` to `"FINISH"`.

                    Do not generate or explain SQL or the report yourself. You are only the planner.
                    """
                )
                msgs.append({"role": "system", "content": system_prompt})
                # Full prompt including the user query and the information retrieved so far
                print(f"**********************information_retrieved:\n {information_retrieved}")
                prompt = f"Main user query: '{user_query}'\n\nInformation retrieved so far:\n{information_retrieved}\n\n Report generated so far:\n{report}\n\n Analyze if the report answer all the main user query and generate a detailed plan:"
                if self.state["user_query"]:
                    prompt += "You may now think of the next step of the plan.\n"
                if self.error_history:
                    prompt += f"\nFor your previous output, the following error was observed:\n{self.error_history[-1]}\n"
                    prompt += "Please correct your response accordingly.\n\n"
                msgs.append({"role": "user", "content": prompt})

                try:
                    chat_completion = self.client.chat.completions.create(model=self.model, messages=msgs)
                    plan_text = chat_completion.choices[0].message.content
                    print(f"plan_text:\n{plan_text}")

                    # Extract JSON from the response
                    pattern = r"```json\s*(.*?)\s*```|({.*?})"
                    match = re.search(pattern, plan_text, re.DOTALL)

                    if match:
                        json_response_str = match.group(1) or match.group(2)
                        json_response = json.loads(json_response_str)

                        # Validate and structure the JSON response
                        response_dict = {}
                        for k, value in json_response.items():
                            if "plan" in k:
                                response_dict["plan"] = value
                            if "next" in k:
                                response_dict["next_agent"] = value
                            if "query" in k:
                                response_dict["query_for_agent"] = value

                        if response_dict and "plan" in response_dict and "next_agent" in response_dict and "query_for_agent" in response_dict:
                            response_dict["sql_results"] = {}
                            response_dict["info"] = information_retrieved
                            return response_dict
                        else:
                            self.error_history.append("Invalid JSON structure: Missing required keys")
                    else:
                        self.error_history.append("No JSON was found in the response")
                except Exception as e:
                    self.error_history.append(f"Error generating plan: {e}")

            # If the loop completes without a successful response, raise an error or handle it accordingly
            return {
                "plan_errors": f"Failed to generate a correct JSON plan after {self.max_iterations} iterations.\nErrors: {self.error_history}"}
        else:
            return {"user_query_error": "User query is not specified"}