# YouTube Multitrack — IA generativa de acordes

App **mobile-first** que toma una URL de YouTube y genera:

| Archivo | Descripción |
|---|---|
| `stems/drums.mp3` | Pista de batería (Demucs) |
| `stems/bass.mp3` | Pista de bajo (Demucs) |
| `stems/vocals.mp3` | Pista de voz (Demucs) |
| `stems/other.mp3` | Resto de instrumentos (Demucs) |
| `click.wav` | Click track / metrónomo (librosa) |
| `guide_voice.wav` | Voz guía + click mezclados |
| `chords.pdf` | Acordes generados con IA (Ollama) |

Todo empaquetado en un **ZIP** listo para descargar.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | **FastAPI** (Python 3.12) |
| Separación de pistas | **Demucs** `htdemucs` (Meta AI) |
| Beat / click | **librosa** |
| Detección de acordes | **librosa** chroma + plantillas |
| Mejora de acordes | **Ollama** (opcional) |
| PDF | **ReportLab** |
| Descarga de audio | **yt-dlp** + ffmpeg |
| Frontend | **React 18** + **Vite** + **Tailwind CSS 3** |
| Producción | **Docker** + **Nginx** |

---

## Instalación rápida (Docker)

```bash
cd youtube_multitrack

# (Opcional) Configura Ollama para acordes mejorados
cat > .env <<'EOF'
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=mistral
EOF

docker compose up --build
```

Si vas a usar mejora de acordes con IA, asegúrate de tener Ollama corriendo y el modelo descargado, por ejemplo:

```bash
ollama pull mistral
ollama serve
```

- Frontend: http://localhost:5173  
- Backend API: http://localhost:8000  
- Docs Swagger: http://localhost:8000/docs

---

## Desarrollo local

### Backend

```bash
cd backend

# Python 3.12+ recomendado
python -m venv .venv && source .venv/bin/activate

# Instalar dependencias del sistema (Ubuntu/Debian)
sudo apt install ffmpeg libsndfile1

pip install -r requirements.txt

# Variables de entorno
export OLLAMA_URL=http://127.0.0.1:11434   # opcional
export OLLAMA_MODEL=mistral                # opcional

uvicorn main:app --reload --port 8000
```

> La primera ejecución descargará el modelo Demucs `htdemucs` (~1 GB). Las siguientes son instantáneas.

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `OLLAMA_URL` | No | URL base de Ollama para mejorar el chord chart. Default: `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | No | Modelo de Ollama usado para estructurar el chord chart. Default: `mistral` |
| `WORK_DIR` | No | Directorio temporal de trabajo. Default: `/tmp/multitrack_jobs` |

---

## Arquitectura y flujo

```
Usuario ──► [React Frontend]
                │
                │ POST /api/jobs { url }
                ▼
         [FastAPI Backend]
                │
         ┌──────┴──────────────────────────────┐
         │  Hilo de fondo (threading.Thread)   │
         │                                      │
         │  1. yt-dlp → original.wav            │
         │  2. Demucs → drums/bass/vocals/other │
         │  3. librosa.beat → click.wav         │
         │  4. Mezcla vocals + click → guide    │
         │  5. librosa.chroma → acordes         │
         │  6. Ollama → chord chart             │
         │  7. ReportLab → chords.pdf           │
         │  8. zipfile → multitrack.zip         │
         └──────────────────────────────────────┘
                │
                │ GET /api/jobs/{id}  (polling cada 2s)
                ▼
         [Frontend muestra progreso]
                │
                │ GET /api/jobs/{id}/download
                ▼
         [Descarga ZIP]
```

---

## API Reference

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/jobs` | Enviar URL de YouTube |
| `GET` | `/api/jobs/{id}` | Consultar estado del job |
| `GET` | `/api/jobs/{id}/download` | Descargar ZIP (solo cuando `status=done`) |
| `DELETE` | `/api/jobs/{id}` | Eliminar job y archivos temporales |
| `GET` | `/health` | Health check |

### POST /api/jobs — Request

```json
{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" }
```

### GET /api/jobs/{id} — Response

```json
{
  "id": "uuid",
  "status": "separating",
  "progress": 35,
  "message": "Separando pistas con IA (Demucs)…",
  "title": "Never Gonna Give You Up",
  "bpm": 113.4,
  "thumbnail": "https://i.ytimg.com/...",
  "error": null
}
```

Estados posibles: `pending` → `downloading` → `separating` → `generating_click` → `detecting_chords` → `creating_pdf` → `packaging` → `done` | `error`

---

## Notas importantes

- **Duración**: canciones de ≤5 min tardan ~3-5 min. Las de 5-10 min pueden tardar 8-12 min.
- **Demucs**: requiere GPU para mayor velocidad. En CPU la separación tarda más.
- **Copyright**: úsalo solo con música de la que tengas derechos o que sea libre de derechos.
- **Ollama**: si no está disponible, los acordes se detectan con el algoritmo de plantillas de librosa (funcional pero menos elaborado).
