"""
YouTube Multitrack API — FastAPI backend.

Endpoints:
  POST /api/jobs          Submit a YouTube URL → returns job_id
  GET  /api/jobs/{id}     Poll job status
  GET  /api/jobs/{id}/download  Stream the result ZIP
"""

import asyncio
import os
import shutil
import threading
import uuid
import zipfile
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl, field_validator

load_dotenv()

app = FastAPI(
    title="YouTube Multitrack",
    description="Generate multitracks + chord PDF from a YouTube URL.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job store (use Redis in production)
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    SEPARATING = "separating"
    GENERATING_CLICK = "generating_click"
    DETECTING_CHORDS = "detecting_chords"
    CREATING_PDF = "creating_pdf"
    PACKAGING = "packaging"
    DONE = "done"
    ERROR = "error"


class Job(BaseModel):
    id: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0        # 0-100
    message: str = ""
    title: Optional[str] = None
    bpm: Optional[float] = None
    thumbnail: Optional[str] = None
    error: Optional[str] = None
    zip_path: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}


_jobs: dict[str, Job] = {}
_jobs_lock = threading.Lock()

WORK_DIR = Path(os.getenv("WORK_DIR", "/tmp/multitrack_jobs"))
WORK_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SubmitRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def must_be_youtube(cls, v: str) -> str:
        v = v.strip()
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("URL must be a YouTube link")
        return v


class JobResponse(BaseModel):
    id: str
    status: str
    progress: int
    message: str
    title: Optional[str]
    bpm: Optional[float]
    thumbnail: Optional[str]
    error: Optional[str]


# ---------------------------------------------------------------------------
# Helper: update job atomically
# ---------------------------------------------------------------------------

def _update_job(job_id: str, **kwargs):
    with _jobs_lock:
        job = _jobs[job_id]
        for k, v in kwargs.items():
            setattr(job, k, v)


# ---------------------------------------------------------------------------
# Background processing pipeline
# ---------------------------------------------------------------------------

def _process_job(job_id: str, youtube_url: str):
    from services.downloader import download_audio
    from services.separator import separate_stems
    from services.click_track import generate_click_track, generate_guide_voice
    from services.chord_detector import detect_chords, enhance_with_ai
    from services.pdf_generator import generate_pdf

    job_dir = WORK_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Download
        _update_job(job_id, status=JobStatus.DOWNLOADING, progress=5, message="Descargando audio de YouTube…")
        info = download_audio(youtube_url, str(job_dir))
        audio_path = info["audio_path"]
        _update_job(
            job_id,
            title=info["title"],
            thumbnail=info["thumbnail"],
            progress=20,
            message="Audio descargado correctamente.",
        )

        # 2. Separate stems
        _update_job(job_id, status=JobStatus.SEPARATING, progress=25, message="Separando pistas con IA (Demucs)…")
        stem_paths = separate_stems(audio_path, str(job_dir))
        _update_job(job_id, progress=55, message="Pistas separadas: drums, bass, vocals, other.")

        # 3. Click track
        _update_job(job_id, status=JobStatus.GENERATING_CLICK, progress=60, message="Generando click track…")
        click_info = generate_click_track(audio_path, str(job_dir))
        bpm = click_info["bpm"]
        _update_job(job_id, bpm=bpm, progress=65, message=f"Click generado · {bpm} BPM")

        # 4. Guide voice
        _update_job(job_id, progress=68, message="Mezclando voz guía…")
        vocals_path = stem_paths.get("vocals", audio_path)
        guide_path = generate_guide_voice(vocals_path, click_info["click_path"], str(job_dir))

        # 5. Chord detection
        _update_job(job_id, status=JobStatus.DETECTING_CHORDS, progress=70, message="Detectando acordes…")
        chord_result = detect_chords(audio_path)
        _update_job(job_id, progress=78, message="Acordes detectados, mejorando con IA (Ollama)…")

        chord_text = enhance_with_ai(
            chord_result["simplified"],
            song_title=info["title"],
            bpm=bpm,
            ollama_url=OLLAMA_URL,
            ollama_model=OLLAMA_MODEL,
        )
        _update_job(job_id, progress=85, message="Acordes generados con IA.")

        # 6. PDF
        _update_job(job_id, status=JobStatus.CREATING_PDF, progress=87, message="Creando PDF de acordes…")
        pdf_path = generate_pdf(
            chord_chart_text=chord_text,
            song_title=info["title"],
            uploader=info.get("uploader", ""),
            bpm=bpm,
            output_dir=str(job_dir),
        )
        _update_job(job_id, progress=92, message="PDF listo.")

        # 7. Package ZIP
        _update_job(job_id, status=JobStatus.PACKAGING, progress=93, message="Empaquetando archivos…")
        zip_path = str(job_dir / "multitrack.zip")
        _build_zip(zip_path, stem_paths, click_info["click_path"], guide_path, pdf_path)

        _update_job(
            job_id,
            status=JobStatus.DONE,
            progress=100,
            message="¡Listo! Descarga tu multitrack.",
            zip_path=zip_path,
        )

    except Exception as exc:
        _update_job(
            job_id,
            status=JobStatus.ERROR,
            progress=100,
            message="Ocurrió un error durante el procesamiento.",
            error=str(exc),
        )


def _build_zip(
    zip_path: str,
    stem_paths: dict,
    click_path: str,
    guide_path: str,
    pdf_path: str,
):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for stem, path in stem_paths.items():
            if os.path.exists(path):
                zf.write(path, f"stems/{stem}.mp3")
        if os.path.exists(click_path):
            zf.write(click_path, "click.wav")
        if os.path.exists(guide_path):
            zf.write(guide_path, "guide_voice.wav")
        if os.path.exists(pdf_path):
            zf.write(pdf_path, "chords.pdf")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/api/jobs", response_model=JobResponse, status_code=202)
def submit_job(req: SubmitRequest):
    """Submit a YouTube URL for processing. Returns a job_id to poll."""
    job_id = str(uuid.uuid4())
    job = Job(id=job_id)
    with _jobs_lock:
        _jobs[job_id] = job

    thread = threading.Thread(
        target=_process_job, args=(job_id, req.url), daemon=True
    )
    thread.start()

    return _job_to_response(job)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    """Poll the status of a job."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@app.get("/api/jobs/{job_id}/download")
def download_result(job_id: str):
    """Download the result ZIP file once the job is DONE."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != JobStatus.DONE:
        raise HTTPException(status_code=409, detail="Job not finished yet")
    if not job.zip_path or not os.path.exists(job.zip_path):
        raise HTTPException(status_code=500, detail="ZIP file not found")

    safe_title = "".join(c for c in (job.title or "multitrack") if c.isalnum() or c in " _-")[:60]
    filename = f"{safe_title}_multitrack.zip"

    return FileResponse(
        path=job.zip_path,
        media_type="application/zip",
        filename=filename,
    )


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(job_id: str):
    """Clean up a finished job and its working directory."""
    with _jobs_lock:
        job = _jobs.pop(job_id, None)
    if job:
        job_dir = WORK_DIR / job_id
        shutil.rmtree(job_dir, ignore_errors=True)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        status=job.status.value,
        progress=job.progress,
        message=job.message,
        title=job.title,
        bpm=job.bpm,
        thumbnail=job.thumbnail,
        error=job.error,
    )
