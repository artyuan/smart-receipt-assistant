from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password")
DB_NAME = os.getenv("db_name")

llm = ChatOpenAI(model="gpt-4o",
                 api_key=OPENAI_API_KEY,
                 temperature=0.1)