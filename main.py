from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GEMINI_API_KEY)
else:
    llm = None
    logger.warning(
        "GEMINI_API_KEY is not set; the API server will start but return a "
        "preview translation instead of calling Gemini."
    )

STYLE_INSTRUCTIONS = {
    "default": "Translate the sentence accurately with a neutral, helpful tone.",
    "hk-mafia-90s": (
        "Translate like a Hong Kong mafia member in the 1990s: a little bit rude, confident, "
        "but never insulting beyond playful toughness."
    ),
}


def _build_prompt_messages(req: TranslateRequest, instruction: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful translation assistant. Produce the translation cleanly "
                "and with the tone requested by the user."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{instruction}\n\n"
                f"Translate the following text from {req.inputLanguage} to {req.outputLanguage}:\n"
                f"{req.text}"
            ),
        },
    ]


def _build_preview_translation(req: TranslateRequest, instruction: str) -> str:
    style_blurb = STYLE_INSTRUCTIONS.get(req.style, STYLE_INSTRUCTIONS["default"])
    return (
        "[Preview translation – Gemini API key is missing]\n"
        f"{style_blurb}\n"
        f"Languages: {req.inputLanguage} → {req.outputLanguage}\n"
        f"Original text: {req.text}"
    )


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    inputLanguage: str
    outputLanguage: str
    style: str = "default"
    instruction: str | None = None


class TranslateResponse(BaseModel):
    translation: str


app = FastAPI(title="Text Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest) -> TranslateResponse:
    instruction = req.instruction or STYLE_INSTRUCTIONS.get(req.style, STYLE_INSTRUCTIONS["default"])
    if llm is None:
        return TranslateResponse(translation=_build_preview_translation(req, instruction))

    messages = _build_prompt_messages(req, instruction)

    try:
        ai_msg = llm.invoke(messages)
        if not ai_msg.content:
            raise ValueError("Empty content returned from LLM.")
        translation = ai_msg.content.strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TranslateResponse(translation=translation)
