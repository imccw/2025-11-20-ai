import streamlit as st
from pathlib import Path
from typing import List, Tuple, Optional
import yt_dlp
import re
import time

# Paths
BASE_DIR = Path(__file__).parent
URLS_FILE = BASE_DIR / "urls.txt"
DOWNLOADS_DIR = Path("/home/imccw/Downloads/audio-downloads")  # or just "/home/imccw/Downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)


def load_urls_from_file(file_path: Path) -> List[str]:
    """Load URLs from a text file."""
    if not file_path.exists():
        return []
    try:
        content = file_path.read_text(encoding="utf-8")
        urls = [line.strip() for line in content.splitlines() if line.strip()]
        return urls
    except Exception as e:
        st.error(f"Error loading URLs from file: {e}")
        return []


def save_urls_to_file(file_path: Path, urls: List[str]) -> None:
    """Save URLs to a text file."""
    try:
        text = "\n".join(urls)
        file_path.write_text(text, encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"Error saving URLs to file: {e}")
        return False


def sanitise_filename_part(value: str) -> str:
    """Clean a string to be safe for filenames."""
    if not value:
        return "unknown"
    
    # Remove invalid characters
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        value = value.replace(char, '_')
    
    # Replace multiple spaces with single space
    value = re.sub(r'\s+', ' ', value)
    
    # Remove leading/trailing spaces
    value = value.strip()
    
    # Limit length
    return value[:100]


def extract_video_info(url: str) -> Tuple[str, str]:
    """Extract video information without downloading."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Untitled')
            video_id = info.get('id', str(int(time.time())))
            return title, video_id
    except Exception:
        # Fallback if we can't extract info
        return "Unknown", str(int(time.time()))


def download_audio_for_owned_content(url: str) -> Tuple[str, str, Path]:
    """
    Download audio from a URL as MP3.
    IMPORTANT: Only use for content you own/have rights to.
    
    Returns: (title, id, output_path)
    """
    try:
        # First, extract video information
        title, video_id = extract_video_info(url)
        
        # Sanitize title for filename
        safe_title = sanitise_filename_part(title)
        
        # Create filename
        filename = f"{safe_title}-{video_id}.mp3"
        output_path = DOWNLOADS_DIR / filename
        
        # Check if file already exists
        if output_path.exists():
            st.info(f"File already exists: {filename}")
            return title, video_id, output_path
        
        # Download audio configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(DOWNLOADS_DIR / f'{safe_title}-{video_id}.%(ext)s'),
            'quiet': False,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [lambda d: None],  # You can add progress hooks here
        }
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get the actual filename that was saved
            downloaded_files = list(DOWNLOADS_DIR.glob(f"{safe_title}-{video_id}.*"))
            if downloaded_files:
                output_path = downloaded_files[0]
        
        return title, video_id, output_path
        
    except Exception as e:
        st.error(f"Error downloading {url}: {e}")
        # Return a fallback filename
        timestamp = str(int(time.time()))
        fallback_path = DOWNLOADS_DIR / f"error-{timestamp}.mp3"
        fallback_path.write_bytes(b"")  # Create empty file
        return "Error", timestamp, fallback_path


def display_downloaded_files():
    """Display all downloaded MP3 files."""
    mp3_files = list(DOWNLOADS_DIR.glob("*.mp3"))
    
    if not mp3_files:
        st.info("No MP3 files downloaded yet.")
        return
    
    st.subheader("📁 Downloaded Files")
    
    # Sort by modification time (newest first)
    mp3_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for i, mp3_file in enumerate(mp3_files, 1):
        file_size = mp3_file.stat().st_size / (1024 * 1024)  # Convert to MB
        col1, col2, col3 = st.columns([6, 2, 2])
        
        with col1:
            st.write(f"**{i}. {mp3_file.name}**")
        
        with col2:
            st.write(f"{file_size:.2f} MB")
        
        with col3:
            with open(mp3_file, "rb") as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name=mp3_file.name,
                    key=f"dl_{i}",
                )


def main():
    st.set_page_config(
        page_title="Batch URL Audio Processor",
        page_icon="🎵",
        layout="wide"
    )
    
    st.title("🎵 Batch URL Audio Processor")
    st.markdown("---")
    
    st.info(
        "**⚠️ IMPORTANT:** Only use this tool for content you own or have rights to download. "
        "Respect copyright laws and terms of service."
    )
    
    # Sidebar for navigation and info
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Go to:",
            ["Process URLs", "View Downloads", "Manage URLs"]
        )
        
        st.markdown("---")
        st.header("Info")
        st.write(f"**Downloads folder:** `{DOWNLOADS_DIR}`")
        st.write(f"**URLs file:** `{URLS_FILE}`")
        
        if st.button("Clear All Downloads", type="secondary"):
            for file in DOWNLOADS_DIR.glob("*"):
                if file.is_file():
                    file.unlink()
            st.success("Downloads folder cleared!")
            st.rerun()
    
    if page == "Process URLs":
        st.header("Process URLs")
        
        # Load URLs from urls.txt
        existing_urls = load_urls_from_file(URLS_FILE)
        
        # User input area
        st.subheader("Add URLs to Process")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_urls_text = st.text_area(
                "Enter URLs (one per line):",
                value="",
                height=150,
                placeholder="https://youtube.com/watch?v=...\nhttps://vimeo.com/...",
                key="url_input",
            )
        
        with col2:
            st.write("**Quick Add**")
            if st.button("Add YouTube Example", type="secondary"):
                st.session_state.url_input = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            
            if st.button("Clear Input", type="secondary"):
                st.session_state.url_input = ""
        
        # Combine URLs
        new_urls = [line.strip() for line in user_urls_text.splitlines() if line.strip()]
        all_urls = list(dict.fromkeys(existing_urls + new_urls))
        
        # Display URLs to process
        st.subheader(f"URLs to Process ({len(all_urls)})")
        
        if all_urls:
            with st.expander("View URLs", expanded=True):
                for i, url in enumerate(all_urls, 1):
                    st.code(f"{i}. {url}", language="text")
            
            # Processing options
            st.subheader("Processing Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                limit = st.number_input(
                    "Limit processing to first N URLs:",
                    min_value=1,
                    max_value=len(all_urls),
                    value=min(5, len(all_urls)),
                    step=1
                )
            
            with col2:
                skip_existing = st.checkbox("Skip existing files", value=True)
            
            with col3:
                auto_save = st.checkbox("Auto-save URLs to file", value=True)
            
            # Process button
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                if auto_save and new_urls:
                    save_urls_to_file(URLS_FILE, all_urls)
                
                # Process limited number of URLs
                urls_to_process = all_urls[:limit]
                
                # Initialize progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                results = []
                successful = 0
                failed = 0
                
                for idx, url in enumerate(urls_to_process, 1):
                    status_text.text(f"Processing {idx}/{len(urls_to_process)}: {url[:80]}...")
                    
                    # Check if file already exists (if skip_existing is enabled)
                    if skip_existing:
                        try:
                            title, video_id = extract_video_info(url)
                            safe_title = sanitise_filename_part(title)
                            filename = f"{safe_title}-{video_id}.mp3"
                            existing_file = DOWNLOADS_DIR / filename
                            
                            if existing_file.exists():
                                st.warning(f"⏭️ Skipping (already exists): {filename}")
                                results.append({
                                    "url": url,
                                    "title": title,
                                    "id": video_id,
                                    "file": str(existing_file),
                                    "status": "skipped"
                                })
                                progress_bar.progress(idx / len(urls_to_process))
                                continue
                        except:
                            pass  # Continue with download if we can't check
                    
                    # Download the audio
                    with st.spinner(f"Downloading {url[:50]}..."):
                        try:
                            title, vid_id, output_path = download_audio_for_owned_content(url)
                            
                            if output_path.exists() and output_path.stat().st_size > 0:
                                results.append({
                                    "url": url,
                                    "title": title,
                                    "id": vid_id,
                                    "file": str(output_path),
                                    "status": "success"
                                })
                                successful += 1
                            else:
                                st.error(f"❌ Download failed for: {url}")
                                failed += 1
                        except Exception as e:
                            st.error(f"❌ Error processing {url}: {e}")
                            failed += 1
                    
                    progress_bar.progress(idx / len(urls_to_process))
                
                # Display results
                status_text.text("✅ Processing complete!")
                
                if results:
                    with results_container:
                        st.subheader("📊 Processing Results")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total", len(urls_to_process))
                        with col2:
                            st.metric("Successful", successful)
                        with col3:
                            st.metric("Failed", failed)
                        
                        # Show detailed results
                        with st.expander("View Detailed Results"):
                            for item in results:
                                status_icon = "✅" if item.get("status") in ["success", "skipped"] else "❌"
                                st.write(f"{status_icon} **{item['title']}** - `{item['file']}`")
        else:
            st.warning("No URLs to process. Please add URLs above.")
    
    elif page == "View Downloads":
        st.header("Downloaded Files")
        display_downloaded_files()
    
    elif page == "Manage URLs":
        st.header("Manage URLs")
        
        # Load current URLs
        current_urls = load_urls_from_file(URLS_FILE)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current URLs in urls.txt")
            if current_urls:
                edited_urls = st.text_area(
                    "Edit URLs (one per line):",
                    value="\n".join(current_urls),
                    height=300,
                    key="edit_urls"
                )
                
                if st.button("💾 Save Changes", type="primary"):
                    new_url_list = [line.strip() for line in edited_urls.splitlines() if line.strip()]
                    if save_urls_to_file(URLS_FILE, new_url_list):
                        st.success(f"Saved {len(new_url_list)} URLs to file!")
                        st.rerun()
            else:
                st.info("No URLs in urls.txt file.")
        
        with col2:
            st.subheader("File Operations")
            
            # Upload URLs from file
            uploaded_file = st.file_uploader(
                "Upload URLs from a text file",
                type=['txt', 'csv'],
                key="url_upload"
            )
            
            if uploaded_file:
                content = uploaded_file.getvalue().decode("utf-8")
                uploaded_urls = [line.strip() for line in content.splitlines() if line.strip()]
                
                st.write(f"Found {len(uploaded_urls)} URLs in uploaded file")
                
                if uploaded_urls and st.button("Add Uploaded URLs"):
                    combined_urls = list(dict.fromkeys(current_urls + uploaded_urls))
                    if save_urls_to_file(URLS_FILE, combined_urls):
                        st.success(f"Added {len(uploaded_urls)} URLs! Total: {len(combined_urls)}")
                        st.rerun()
            
            # Clear URLs
            st.markdown("---")
            st.warning("Danger Zone")
            if st.button("🗑️ Clear All URLs", type="secondary"):
                if URLS_FILE.exists():
                    URLS_FILE.unlink()
                    st.success("URLs file cleared!")
                    st.rerun()


if __name__ == "__main__":
    main()