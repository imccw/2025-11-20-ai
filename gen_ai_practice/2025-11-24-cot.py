import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0,
    api_key=os.getenv("GEMINI_API_KEY")
)
prompt_template = """
Question: 11 factories can make 22 cars per hour. How much time would it take 22 factories to make 88 cars?
Answer: Let me solve this step by step:
1. A factory can make 22/11 = 2 cars per hour.
2. 22 factories can make 22 * 2 = 44 cars per hour.
3. Making 88 cars would take 88 / 44 = 2 hours.

Therefore, the answer is 2 hours.

Now, solve this new problem using the same step-by-step approach:
Question: {question}
Answer:
"""
prompt = PromptTemplate(
    input_variables=["question"],
    template=prompt_template
)

chain = prompt | llm
def solve_math_problem(problem):
    try:
        response = chain.invoke({"question": problem})
        print(f"Problem: {problem}\n")
        print(f"Solution:\n{response.content}\n")
        print("-" * 50 + "\n")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    new_problem = """5 people can create 5 donuts every 5 minutes.
                     How much time would it take 25 people to make 100 donuts?
                     Return the answer immediately."""
    solve_math_problem(new_problem)
