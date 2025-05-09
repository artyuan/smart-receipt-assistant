from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("HOST")
DB_PORT = os.getenv("PORT")
DB_USER = os.getenv("USER")
DB_PASSWORD = os.getenv("PASSWORD")
DB_NAME = os.getenv("DB_NAME")
MODEL = "gpt-4o"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

llm = ChatOpenAI(model=MODEL,
                 api_key=OPENAI_API_KEY,
                 temperature=0.1)