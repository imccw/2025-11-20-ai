import os
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.0,
    api_key=GEMINI_API_KEY
)

tools = load_tools(["llm-math"], llm=llm)

prompt = PromptTemplate.from_template("""
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda retry_state: print(
        f"\nFailed after performing {retry_state.attempt_number} attempts"
    )
)
def execute_with_retry(question):
    response = agent_executor.invoke({"input": question})
    return response["output"]

if __name__ == "__main__":
    question = "What's the result of an investment of $10,000 growing at 8% annually for 5 years with compound interest?"
    # question = "What's the date human will become extinct if we do not do anything to mitigate pollution?"
    print("\n" + "=" * 50)
    print(f"Question: {question}")
    try:
        result = execute_with_retry(question)
        print("\nResult:", result)
    except Exception as e:
        print(f"Error: {str(e)}")
