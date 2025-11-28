import os
from enum import Enum

import google.ai.generativelanguage_v1beta as genai

try:
    _ = genai.GenerationConfig.MediaResolution
except AttributeError:
    # Provide a minimal enum so langchain_google_genai can import the member.
    class MediaResolution(Enum):
        MEDIA_RESOLUTION_UNSPECIFIED = 0
        MEDIA_RESOLUTION_LOW = 1
        MEDIA_RESOLUTION_MEDIUM = 2
        MEDIA_RESOLUTION_HIGH = 3

    genai.GenerationConfig.MediaResolution = MediaResolution

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from langchain_community.document_loaders import WebBaseLoader
from langchain_google_genai import GoogleGenerativeAI

from langchain_core.prompts import PromptTemplate
from langchain_core.prompts.base import format_document
from langchain_core.output_parsers import StrOutputParser


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set; add it to .env or the environment.")

DEFAULT_WEB_PAGE = "https://blog.google/technology/ai/google-gemini-ai"

llm = GoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0,
    google_api_key=API_KEY,
)

doc_prompt = PromptTemplate.from_template("{page_content}")
llm_prompt = PromptTemplate.from_template(
    """Write a concise summary of the following:

{text}

CONCISE SUMMARY:"""
)

stuff_chain = (
    {
        "text": lambda docs: "\n\n".join(
            format_document(doc, doc_prompt) for doc in docs
        )
    }
    | llm_prompt
    | llm
    | StrOutputParser()
)

app = FastAPI()


@app.get("/summaries/web")
def summarize_web(
    url: str = Query(
        DEFAULT_WEB_PAGE,
        description="URL of the web page to summarize",
    )
):
    """Load a web document, summarize it via the Gemini chain, and return the text."""

    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Cannot load URL: {exc}")

    if not docs:
        raise HTTPException(status_code=404, detail="No documents were retrieved.")

    if not docs[0].page_content.strip():
        raise HTTPException(status_code=422, detail="Document contains no text.")

    try:
        summary = stuff_chain.invoke(docs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LLM chain failed: {exc}")

    return {"url": url, "summary": summary}
