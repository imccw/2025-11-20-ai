import os, base64
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# Load .env file containing GEMINI_API_KEY=xxxx
load_dotenv()

# Initialise Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0,
    api_key=os.getenv("GEMINI_API_KEY")
)

# 1. SET YOUR VIDEO PATH HERE
# ---------------------------------------------------------
# Example 1: If hyena.mp4 is in the SAME folder as this script:
# video_file_path = "hyena.mp4"
#
# Example 2: If your file is inside a "videos" folder:
# video_file_path = "videos/hyena.mp4"
# ---------------------------------------------------------
video_file_path = "media/hyena.mp4"

# Read & Base64 encode the video
with open(video_file_path, "rb") as f:
    encoded_video = base64.b64encode(f.read()).decode()

# Build prompt
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an expert video analyst. Provide accurate scene interpretation."),
    ("human", [
        {
            "type": "text",
            "text": "{analysis_request}"
        },
        {
            "type": "media",
            "data": "{video_data}",
            "mime_type": "{mime_type}"
        }
    ])
])

# Build the chain
chain = prompt | llm

print("Analyzing video...")

# Call Gemini
response = chain.invoke({
    "analysis_request": "Describe what's happening in this video.",
    "video_data": encoded_video,
    "mime_type": "video/mp4"
})

print("Analysis completed.")
print("\nRESULTS:\n" + "-" * 40)
print(response.content)
