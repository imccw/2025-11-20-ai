import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

DEFAULT_YOUTUBE_URL = "https://www.youtube.com/watch?v=p-d5S9JHYQQ"


FORMATS = [
    (
        "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/"
        "bestvideo[height<=480]+bestaudio/best[ext=mp4]/best"
    ),
    "bestvideo[height<=480]+bestaudio/best",
    "best",
]


def download_video(youtube_url: str):
    """Download the provided YouTube URL into a temporary directory."""
    temp_dir = tempfile.TemporaryDirectory(prefix="youtube-dl-")
    output_template = Path(temp_dir.name) / "video.%(ext)s"
    last_error = None
    for fmt in FORMATS:
        print(f"Trying format '{fmt}'...")
        ydl_opts = {
            "format": fmt,
            "outtmpl": str(output_template),
            "noplaylist": True,
            "quiet": False,
            "no_warnings": True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                downloaded_path = Path(ydl.prepare_filename(info))
            return temp_dir, downloaded_path, info
        except DownloadError as exc:
            print(f"Format '{fmt}' failed: {exc}")
            last_error = exc
    temp_dir.cleanup()
    raise last_error or RuntimeError("Unknown failure while downloading video.")


def default_save_path(info: dict, downloaded_path: Path) -> Path:
    """Build a safe Downloads path defaulting to '{title}-{id}{ext}'. """
    downloads_dir = Path("/home/imccw/Downloads").expanduser()
    downloads_dir.mkdir(exist_ok=True, parents=True)

    title = str(info.get("title") or downloaded_path.stem)
    video_id = str(info.get("id") or "")
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
    base_name = safe_title or downloaded_path.stem
    if video_id:
        base_name = f"{base_name}-{video_id}"

    ext = downloaded_path.suffix or ".mp4"
    candidate = downloads_dir / f"{base_name}{ext}"
    i = 1
    while candidate.exists():
        candidate = downloads_dir / f"{base_name}-{i}{ext}"
        i += 1
    return candidate


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a YouTube video and let the user save it via a GUI dialog."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_YOUTUBE_URL,
        help="YouTube video URL to download (default uses a sample link).",
    )
    args = parser.parse_args()

    print(f"Downloading {args.url}...")
    try:
        temp_dir, downloaded_path, info = download_video(args.url)
    except Exception as exc:
        print(f"Failed to download the video: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Downloaded {downloaded_path.name}. Saving to Downloads...")
    try:
        destination = default_save_path(info, downloaded_path)
        shutil.copy2(downloaded_path, destination)
        print(f"Saved video to {destination}")
    except OSError as exc:
        temp_dir.cleanup()
        print(f"Failed to save the video: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        temp_dir.cleanup()


if __name__ == "__main__":
    main()
