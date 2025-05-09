import re
import openai
from src.config import OPENAI_API_KEY, MODEL


class ReportWriterAgent:
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

        if self.state.get("plan"):
            info += f"Plan:\n{self.state['plan']}\n\n"

        if self.state.get("sql_results"):
            info += "SQL Results:\n"
            for query, results in self.state["sql_results"].items():
                info += f"Query: {query}\n"
                info += f"Result:\n{results}\n\n"
            self.state['info'] += info

        if not info:
            info = "No information retrieved yet."

        return info

    def generate_report(self) -> str:
        """
        Use OpenAI API to generate a report based on the information in AgentState, retrying up to max_iterations.
        The report content will start after a specific keyword to allow for easy extraction.
        """
        for iteration in range(self.max_iterations):
            msgs = []
            # Prepare the information retrieved so far
            information_retrieved = self._prepare_information_retrieved()
            print("###################################")
            print(information_retrieved)
            print("###################################")
            if "full_report" not in self.state:
                self.state["full_report"] = "No report generated so far"
            report = self.state["full_report"]

            # System prompt
            system_prompt = (
                "You are an expert data analyst and report writer. Your task is to generate a clear, concise, and professional report in markdown format "
                "that helps the user understand their day-to-day grocery spending across different supermarkets. Use the data provided to extract key insights, "
                "highlight spending patterns, and make meaningful comparisons between supermarkets, time periods, or product categories.\n\n"
                "Structure the report using markdown with appropriate headings (e.g., '# Weekly Grocery Spending Report'). You may start the report directly with a markdown title, "
                "or, if you include any introductory content, begin the main analysis after the keyword 'REPORT_START'.\n\n"
                "The report should be:\n"
                "- Written in a user-friendly but professional tone\n"
                "- Structured with clear sections and logical flow\n"
                "- Focused on actionable insights (e.g., where the user spends the most, how spending changes over time)\n"
                "- Enhanced with summaries, bullet points, and comparisons when helpful"
            )
            msgs.append({"role": "system", "content": system_prompt})

            # Full prompt including the information retrieved so far
            prompt = f"Information retrieved so far:\n{information_retrieved}\n\n The report generated so far:\n{report}\n\nIf the report hasn't been generated, create one based on the retrieved information and if there is a report improve it using the retrieved information.\n\nREPORT_START:"

            if self.state.get('query_for_agent'):
                prompt += f"\nInstruction: {self.state['query_for_agent']}"

            msgs.append({"role": "user", "content": prompt})

            try:
                chat_completion = self.client.chat.completions.create(model=self.model, messages=msgs)
                report_text = chat_completion.choices[0].message.content
                print(f"report_text:\n{report_text}")

                # Check for markdown header (e.g., # Report Title)
                pattern = r"(?:report[_\s]*start[:\s]*)?(# .*)"
                match = re.search(pattern, report_text, re.DOTALL | re.IGNORECASE)

                if match:
                    report_content = match.group(1).strip()
                    self.state["full_report"] = report_content
                    return {"full_report": report_content}
                else:
                    self.error_history.append(
                        "No report content found after 'REPORT_START' or no markdown header detected.")
            except Exception as e:
                self.error_history.append(f"Error generating report: {e}")

        # If the loop completes without a successful response, return an error message
        return {
            "report_error": f"Failed to generate the report after {self.max_iterations} iterations.\nErrors: {self.error_history}"}
