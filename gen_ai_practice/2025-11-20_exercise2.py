import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=GEMINI_API_KEY
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that translates {input_language} to {output_language}."
        ),
        (
            "human",
            "{input}"
        ),
    ]
)

chain = prompt | llm

ai_msg = chain.invoke(
    {
        "input_language": "English",
        "output_language": "Bahasa Malaysia",
        "input": "I like to eat cookies on sunday"
    }
)

print(ai_msg.content)
