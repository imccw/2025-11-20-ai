import os, base64
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def encode_image(image_content: bytes) -> str:
    return base64.b64encode(image_content).decode()

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)) -> Dict[str, str]:
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, detail="Invalid file type. Only JPEG and PNG are allowed.")

    # Validate file size
    if file.size and file.size > 10_000_000:
        raise HTTPException(400, detail="File too large. Maximum size is 10MB.")

    try:
        contents = await file.read()
        image = encode_image(contents)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a nutrition expert capable of analysing food images and providing detailed nutritional advice."),
            ("human", [
                {
                    "type": "text",
                    "text": """
Assess the food in the image and reply only with a JSON object that estimates the macronutrients for a typical portion.
Use the keys "protein_g", "carbs_g", and "fat_g" with gram estimates or ranges (e.g., "20-25g").
Do not include any other commentary, HTML, or formatting—just the JSON object on one line.
If the picture is unclear, note uncertainty within the values using ranges or qualifiers inside the JSON.
"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image}",
                        "detail": "high",
                    },
                }
            ])
        ])

        chain = prompt | llm
        res = await chain.ainvoke({})

        return {"analysis": res.content}

    except Exception:
        raise HTTPException(500, detail="An error occurred while processing the image")
