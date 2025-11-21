import os
from dotenv import load_dotenv
from langsmith import uuid7
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Load environment variables
load_dotenv()

# LLM setup
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0,
    api_key=os.getenv("GEMINI_API_KEY")
)

# Prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Answer all questions to the best of your ability."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Build the chain
chain = prompt | llm

# In-memory store for sessions
store = {}

def get_message_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Chain with history enabled
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_message_history,
    input_messages_key="input",
    history_messages_key="history"
)


def run_interactive_chat():
    """Prompt for user input, send it through the chain, and print the assistant reply."""
    session_id = uuid7()
    print("\nStarting chat... Type 'quit' or 'exit' to end the conversation.")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue

        try:
            response = chain_with_history.invoke(
                {"input": user_input},
                {"configurable": {"session_id": session_id}}
            )
            ai_message = getattr(response, "content", None) or str(response)
            print(f"AI: {ai_message}")
        except Exception as exc:
            print(f"An error occurred: {exc}")

    print("\nChat ended.")


if __name__ == "__main__":
    run_interactive_chat()
