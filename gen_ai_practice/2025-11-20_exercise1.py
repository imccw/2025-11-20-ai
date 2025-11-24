import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI  # Fixed import

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)

messages = [
    {
        "role": "system",  # Use key-value pairs
        "content": "You are a helpful assistant that translates English to Bahasa Malaysia."
    },
    {
        "role": "user",  # Use "user" instead of "human"
        "content": "I want to go to imago today"
    }
]

ai_msg = llm.invoke(messages)  # Fixed variable name
print(ai_msg.content)