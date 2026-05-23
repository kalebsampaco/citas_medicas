"""Audio stem separation using Demucs (htdemucs model)."""

import os
import shutil
import subprocess


STEMS = ["drums", "bass", "vocals", "other"]


def separate_stems(audio_path: str, output_dir: str) -> dict[str, str]:
    """
    Run Demucs on `audio_path` and move stems into `output_dir`.

    Returns a dict mapping stem name -> absolute file path.
    """
    stems_out = os.path.join(output_dir, "stems_raw")
    os.makedirs(stems_out, exist_ok=True)

    cmd = [
        "python",
        "-m",
        "demucs",
        "--name",
        "htdemucs",
        "--out",
        stems_out,
        "--mp3",
        "--mp3-bitrate",
        "320",
        audio_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed: {result.stderr}")

    # Demucs writes to: <stems_out>/htdemucs/<track_name>/<stem>.mp3
    track_name = "original"
    demucs_track_dir = os.path.join(stems_out, "htdemucs", track_name)

    stem_paths: dict[str, str] = {}
    for stem in STEMS:
        src = os.path.join(demucs_track_dir, f"{stem}.mp3")
        dst = os.path.join(output_dir, f"{stem}.mp3")
        if os.path.exists(src):
            shutil.move(src, dst)
            stem_paths[stem] = dst

    # Clean up Demucs raw output folder
    shutil.rmtree(stems_out, ignore_errors=True)

    return stem_paths
