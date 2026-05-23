"""YouTube audio downloader using yt-dlp."""

import os
import yt_dlp


def download_audio(youtube_url: str, output_dir: str) -> dict:
    """
    Download audio from a YouTube URL.

    Returns a dict with:
        - audio_path: absolute path to the downloaded WAV file
        - title: video title
        - duration: duration in seconds
        - thumbnail: thumbnail URL
    """
    output_template = os.path.join(output_dir, "original.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)

    audio_path = os.path.join(output_dir, "original.wav")

    return {
        "audio_path": audio_path,
        "title": info.get("title", "Unknown"),
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "uploader": info.get("uploader", ""),
    }
