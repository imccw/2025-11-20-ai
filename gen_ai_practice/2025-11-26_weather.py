import os, json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

class WeatherReport(BaseModel):
    city: str = Field(description="Name of the city")
    temperature: float = Field(description="Current temperature in Celsius")
    conditions: List[str] = Field(description="List of weather conditions")
    humidity: int = Field(description="Humidity percentage")
    wind_speed: float = Field(description="Wind speed in km/h")

output_parser = JsonOutputParser(pydantic_object=WeatherReport)

chat_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a weather expert. Provide current weather information in the specified JSON format.
Make realistic estimations based on the season and location."""
    ),
    (
        "human",
        "{request}\n{format_instructions}"
    )
])

chain = chat_prompt | llm | output_parser

response = chain.invoke({
    "request": "What's the weather like in Malaysia today?",
    "format_instructions": output_parser.get_format_instructions()
})

print("\nResponse:")
print(json.dumps(response, indent=4))
