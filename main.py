from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from pypdf import PdfReader

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DIABETES_PDF_PATH = BASE_DIR / "media" / "diabetes.pdf"

def _load_diabetes_text(path: Path) -> str:
    if not path.exists():
        logger.warning("diabetes.pdf was not found at %s", path)
        return ""

    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        logger.error("Failed to open diabetes.pdf: %s", exc)
        return ""

    pages: list[str] = []
    for page in reader.pages:
        try:
            content = page.extract_text()
        except Exception as exc:
            logger.debug("Unable to extract text from a page: %s", exc, exc_info=True)
            continue
        if content:
            pages.append(content.strip())

    documents = "\n\n".join(pages).strip()
    if not documents:
        logger.warning("diabetes.pdf was read but no text could be extracted")
    return documents

DIABETES_DOCUMENT = _load_diabetes_text(DIABETES_PDF_PATH)
DIABETES_SYSTEM_PROMPT = (
    "You are a concise medical research assistant. Answer only from the provided diabetes.pdf text. "
    "Do not hallucinate, and if the document lacks an answer, say so clearly."
)

def _build_diabetes_prompt(question: str) -> str:
    return (
        "Document excerpt from diabetes.pdf:\n"
        f"{DIABETES_DOCUMENT}\n\n"
        f"Question:\n{question}\n\n"
        "Answer using only the text above. If the document does not contain the answer, "
        'respond with "I do not have enough information to answer that.".'
    )

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


class DiabetesResponse(BaseModel):
    question: str
    answer: str


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


@app.get("/ask", response_model=DiabetesResponse)
def answer_diabetes_question(question: str = Query(..., min_length=1)) -> DiabetesResponse:
    if not DIABETES_DOCUMENT:
        raise HTTPException(
            status_code=503, detail="diabetes.pdf is missing or unreadable in the media directory."
        )

    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured, so the diabetes question cannot be answered.",
        )

    messages = [
        {"role": "system", "content": DIABETES_SYSTEM_PROMPT},
        {"role": "user", "content": _build_diabetes_prompt(question)},
    ]

    try:
        ai_msg = llm.invoke(messages)
        if not ai_msg.content:
            raise ValueError("LLM returned an empty response.")
        answer = ai_msg.content.strip()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return DiabetesResponse(question=question, answer=answer)
