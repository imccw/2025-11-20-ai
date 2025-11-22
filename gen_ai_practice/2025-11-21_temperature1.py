import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=1.0,
    api_key=GEMINI_API_KEY
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Answer all questions to the best of your ability."),
    ("human", "{input}")
])

chain = prompt | llm

print("\nStarting chat... Type 'quit' or 'exit' to end the conversation.")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit"]:
        break

    try:
        response = chain.invoke({"input": user_input})
        print(f"AI: {response.content}")

    except Exception as e:
        print(f"An error occurred: {e}")

print("\nChat ended.")
