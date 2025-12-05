import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0, api_key=GEMINI_API_KEY)

conn_string = 'postgresql://postgres:0@localhost/books_db'
engine = create_engine(conn_string)

db = SQLDatabase.from_uri(conn_string)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

sql_agent = create_sql_agent(
    toolkit=toolkit,
    llm=llm,
    verbose=True,
    max_iterations=5,
    allow_dangerous_code=False
)
sql_agent.handle_parsing_errors = True

user_query = """which book is the latest? and who has the highest salary?"""
res = sql_agent.invoke(user_query)

print(res["output"])
