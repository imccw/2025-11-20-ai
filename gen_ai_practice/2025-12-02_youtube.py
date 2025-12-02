import base64
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from yt_dlp import YoutubeDL

# Load .env file containing GEMINI_API_KEY=xxxx
load_dotenv()

# Initialise Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0,
    api_key=os.getenv("GEMINI_API_KEY")
)

DEFAULT_YOUTUBE_LINK = (
    "https://www.youtube.com/watch?v=p-d5S9JHYQQ"
)
FALLBACK_VIDEO_PATH = Path("media/hyena.mp4")
DEFAULT_ANALYSIS_REQUEST = "Describe what's happening in this video."


def prompt_youtube_link(default_link: str) -> str:
    """Ask the user for a YouTube URL, falling back to the default if they skip."""
    provided = input(f"Enter YouTube link [{default_link}]: ").strip()
    return provided or default_link


def prompt_analysis_request(default_request: str) -> str:
    """Ask the user to customize the analysis request text."""
    provided = input(f"Enter analysis request [{default_request}]: ").strip()
    return provided or default_request


def base64_from_file(video_path: Path) -> str:
    """Return the base64-encoded contents of `video_path`."""
    with open(video_path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def download_youtube_media(youtube_url: str) -> str:
    """Download a YouTube video to a temporary file and return the encoded data."""
    with tempfile.TemporaryDirectory(prefix="youtube-video-") as tmpdir:
        tmp_path = Path(tmpdir) / "video.%(ext)s"
        ydl_opts = {
            # Prefer a single 360p MP4 stream so no merging (and ffmpeg) is required.
            "format": "bestvideo[height<=360][ext=mp4]/best[height<=360]/best",
            "outtmpl": str(tmp_path),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            downloaded_path = Path(ydl.prepare_filename(info))
            return base64_from_file(downloaded_path)


def get_encoded_video(youtube_url: str) -> str:
    """Try downloading the requested YouTube video, falling back when needed."""
    try:
        return download_youtube_media(youtube_url)
    except Exception as err:  # pragma: no cover - best-effort download
        print(
            f"Unable to fetch YouTube video ({youtube_url}): {err}\n"
            "Falling back to the bundled sample video."
        )
        return base64_from_file(FALLBACK_VIDEO_PATH)


youtube_url = prompt_youtube_link(DEFAULT_YOUTUBE_LINK)

encoded_video = get_encoded_video(youtube_url)

analysis_request = prompt_analysis_request(DEFAULT_ANALYSIS_REQUEST)

print(f"Using YouTube link: {youtube_url}")

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
    "analysis_request": analysis_request,
    "video_data": encoded_video,
    "mime_type": "video/mp4"
})

print("Analysis completed.")
print("\nRESULTS:\n" + "-" * 40)
print(response.content)
