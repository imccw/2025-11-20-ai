import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.output_parsers import DatetimeOutputParser

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

output_parser = DatetimeOutputParser()

chat_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You always reply to questions only in datetime patterns"
        ),
        (
            "human",
            "{request} \n {format_instructions}"
        ),
    ]
)

chain = chat_prompt | llm

ai_msg = chain.invoke(
    {
        "request": "When was the first human landing on the moon?",
        "format_instructions": output_parser.get_format_instructions()
    }
)

print(output_parser.get_format_instructions())
print("\n")
print(ai_msg.content)
