# Text Translator Frontend

This repo contains a lightweight static UI for a translator like the reference screenshot. It is purely front-end, so you can open `index.html` in any browser, or serve it with Python:

```bash
python -m http.server 4173
```

Then visit http://localhost:4173 in your browser.

The UI now calls `POST http://localhost:8000/translate` with `{ text, inputLanguage, outputLanguage, style, instruction }`,
so the backend can honor tone instructions like `"hk-mafia-90s"` and a Cantonese output request. A FastAPI server is included:

1. Install the backend dependencies (ideally inside the `.venv`):

```bash
pip install -r requirements.txt
```

2. Create a `.env` with your Gemini key (same as `main.py`) and start the server:

```bash
uvicorn main:app --reload --port 8000
```

If you skip the Gemini key, the backend still starts up and returns a preview translation (so the UI keeps working without hitting Gemini).

3. Refresh `index.html` (served via `python -m http.server 4173` or similar) to send requests to the FastAPI route.

`script.js` already sends `style`/`instruction` and has a fallback translation when the backend is unreachable, so you can test locally before Gemini is set up.
