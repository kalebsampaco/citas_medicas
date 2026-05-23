"""
Chord detection via librosa chroma features + optional OpenAI enhancement.

Pipeline:
  1. Extract chroma_cqt features from the audio.
  2. Match each segment to the closest chord template (24 chords).
  3. Simplify the sequence by merging consecutive identical chords.
  4. (Optional) Send the raw sequence to OpenAI to produce a clean,
     formatted chord chart with section labels.
"""

import os
import textwrap
from typing import Optional

import librosa
import numpy as np


# ---------------------------------------------------------------------------
# Chord templates (normalised chroma vectors for 12 major + 12 minor chords)
# ---------------------------------------------------------------------------

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Major triad intervals: root, M3, P5  (0, 4, 7)
# Minor triad intervals: root, m3, P5  (0, 3, 7)

def _build_templates() -> tuple[list[str], np.ndarray]:
    names: list[str] = []
    templates: list[np.ndarray] = []
    for i, note in enumerate(NOTES):
        # Major
        vec = np.zeros(12)
        for interval in (0, 4, 7):
            vec[(i + interval) % 12] = 1.0
        names.append(f"{note}")
        templates.append(vec / np.linalg.norm(vec))
        # Minor
        vec_m = np.zeros(12)
        for interval in (0, 3, 7):
            vec_m[(i + interval) % 12] = 1.0
        names.append(f"{note}m")
        templates.append(vec_m / np.linalg.norm(vec_m))
    return names, np.array(templates)


CHORD_NAMES, CHORD_TEMPLATES = _build_templates()


def _chroma_to_chord(chroma_frame: np.ndarray) -> str:
    """Return the closest chord name for a single chroma vector."""
    norm = np.linalg.norm(chroma_frame)
    if norm < 1e-6:
        return "N"  # silence / no chord
    frame_n = chroma_frame / norm
    scores = CHORD_TEMPLATES @ frame_n
    return CHORD_NAMES[int(np.argmax(scores))]


def detect_chords(
    audio_path: str,
    hop_length: int = 4096,
    segment_seconds: float = 2.0,
) -> dict:
    """
    Detect chords from `audio_path`.

    Returns a dict with:
        - chord_sequence: list of (time_sec, chord_name) tuples
        - simplified: collapsed list removing consecutive duplicates
        - bpm_sections: dict mapping chord -> approximate beat count
    """
    y, sr = librosa.load(audio_path, mono=True)

    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length)

    # Aggregate over `segment_seconds` windows for stability
    frames_per_seg = max(1, int(segment_seconds * sr / hop_length))
    chord_sequence: list[tuple[float, str]] = []
    for start in range(0, chroma.shape[1], frames_per_seg):
        seg = chroma[:, start : start + frames_per_seg]
        avg_chroma = seg.mean(axis=1)
        chord = _chroma_to_chord(avg_chroma)
        chord_sequence.append((float(times[start]), chord))

    # Simplify: merge consecutive identical chords
    simplified: list[tuple[float, str]] = []
    for time_sec, chord in chord_sequence:
        if not simplified or simplified[-1][1] != chord:
            simplified.append((time_sec, chord))

    return {
        "chord_sequence": chord_sequence,
        "simplified": simplified,
    }


# ---------------------------------------------------------------------------
# OpenAI enhancement (optional)
# ---------------------------------------------------------------------------

def enhance_with_ai(
    simplified: list[tuple[float, str]],
    song_title: str,
    bpm: float,
    openai_api_key: Optional[str] = None,
) -> str:
    """
    Use OpenAI GPT to produce a structured, human-readable chord chart.
    Falls back to a plain text chart if no API key is provided.
    """
    # Plain-text fallback
    plain = _build_plain_chart(simplified, song_title, bpm)

    if not openai_api_key:
        return plain

    try:
        from openai import OpenAI

        raw_sequence = " | ".join(
            f"[{_fmt_time(t)}] {c}" for t, c in simplified
        )

        prompt = textwrap.dedent(
            f"""
            You are a professional music arranger. Given the raw chord detection
            output below for the song "{song_title}" at {bpm} BPM, create a clean,
            structured chord chart.

            Rules:
            - Organise chords into sections (Intro, Verse, Chorus, Bridge, Outro)
              based on repeating patterns.
            - Use standard chord notation (C, Dm, G7, Am, etc.).
            - Write each bar as 4 beats. Use | to separate bars.
            - Include a tempo header: Tempo: {bpm} BPM.
            - Output ONLY the chord chart text, no explanation.

            Raw chord sequence:
            {raw_sequence}
            """
        ).strip()

        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3,
        )
        return response.choices[0].message.content or plain
    except Exception:
        return plain


def _fmt_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"


def _build_plain_chart(
    simplified: list[tuple[float, str]], song_title: str, bpm: float
) -> str:
    lines = [
        f"CHORD CHART — {song_title}",
        f"Tempo: {bpm} BPM",
        "",
    ]
    for time_sec, chord in simplified:
        lines.append(f"  [{_fmt_time(time_sec)}]  {chord}")
    return "\n".join(lines)
