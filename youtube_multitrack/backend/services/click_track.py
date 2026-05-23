"""Click track generator using librosa beat detection."""

import os

import librosa
import numpy as np
import soundfile as sf


def generate_click_track(audio_path: str, output_dir: str) -> dict:
    """
    Detect BPM and beat positions from `audio_path`, then write a click WAV.

    Returns a dict with:
        - click_path: absolute path to click.wav
        - bpm: detected tempo in BPM
        - beat_times: list of beat positions in seconds
    """
    y, sr = librosa.load(audio_path, mono=True)

    # Detect tempo and beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # Generate click audio using librosa
    click_audio = librosa.clicks(
        times=beat_times,
        sr=sr,
        click_freq=1000.0,  # Hz – bright click
        click_duration=0.05,
        length=len(y),
    )

    click_path = os.path.join(output_dir, "click.wav")
    sf.write(click_path, click_audio.astype(np.float32), sr)

    bpm = float(np.round(tempo, 1)) if np.ndim(tempo) == 0 else float(np.round(tempo[0], 1))

    return {
        "click_path": click_path,
        "bpm": bpm,
        "beat_times": beat_times,
    }


def generate_guide_voice(
    vocals_path: str, click_path: str, output_dir: str
) -> str:
    """
    Mix vocals stem with click track to produce a guide voice file.

    Returns the absolute path to guide_voice.wav.
    """
    vocals, sr_v = librosa.load(vocals_path, mono=True)
    click, sr_c = librosa.load(click_path, sr=sr_v, mono=True)

    # Pad/trim to same length
    length = max(len(vocals), len(click))
    vocals = np.pad(vocals, (0, max(0, length - len(vocals))))
    click = np.pad(click, (0, max(0, length - len(click))))

    # Mix: vocals at full volume, click at -6 dB
    guide = vocals + (click * 0.5)

    # Normalize to prevent clipping
    peak = np.max(np.abs(guide))
    if peak > 1.0:
        guide = guide / peak

    guide_path = os.path.join(output_dir, "guide_voice.wav")
    sf.write(guide_path, guide.astype(np.float32), sr_v)
    return guide_path
