# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

## Project Overview

LectureMind is an AI-powered lecture video analysis and summarization platform. It processes lecture videos through a multi-stage pipeline: video upload, HLS transcoding, ASR transcription, slide detection, OCR, knowledge extraction, and RAG-based chatbot Q&A.

**Architecture**: Django REST backend + React frontend + Docker Compose for deployment. The backend uses a custom DAG-based async task processor for video processing pipelines.

## Common Commands

### Backend (Django)

```bash
cd server/app

# Setup
conda env create -f environment.yml  # or: pip install -r requirements.txt
conda activate LectureMind
python manage.py migrate

# Development
python manage.py runserver           # API server — port from BACKEND_PORT env (default :8000)
python manage.py process_async_task  # Task processor (run in separate terminal)

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell

# Admin
python manage.py createsuperuser
python manage.py shell

# RAG Evaluation
python manage.py evaluate_rag --video <uuid> --questions 20
python manage.py evaluate_rag --video <uuid> --question "Q1,Q2" --question_count 10
```

### Frontend (React)

```bash
cd frontend

# Setup
pnpm install

# Development
pnpm start                           # Dev server on :3000
pnpm build                           # Production build
pnpm test                            # Run tests
```

### Docker

```bash
# Build and start all services
cp .env.example .env   # then fill in secrets
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f web
docker compose logs -f worker

# Rebuild a single service
docker compose build web
docker compose up -d web
```

### Environment Setup

Copy `.env.example` to `.env` and configure:
- `DASHSCOPE_API_KEY` — Alibaba DashScope for ASR and LLM
- `COS_SECRECT_ID`, `COS_SECRECT_KEY`, `COS_REGION`, `COS_BUCKET` — Tencent COS for audio file hosting
- `BACKEND_PORT` — backend port (default `8000`)
- `FRONTEND_PORT` — frontend port (default `3000`)

See `docs/CONFIGURATION.md` for the full list of configurable variables.

## Project Structure

```
LectureMind/
├── docker-compose.yml               # Compose: web + worker + frontend
├── .env.example                     # All configurable variables with defaults
│
├── server/
│   ├── Dockerfile                   # 2-stage backend image (builder + runtime)
│   ├── docker-entrypoint.sh         # migrate → collectstatic → web|worker
│   ├── requirements.txt             # Python dependencies (incl. gunicorn)
│   ├── environment.yml              # Conda environment
│   └── app/
│       ├── manage.py                # Django entry point
│       ├── videoapp/
│       │   ├── settings.py          # All paths/ports read from env vars
│       │   └── urls.py              # Root URL routing
│       └── api/
│           ├── models.py            # Episode, Video, Thumbnail, Transcript,
│           │                        # VideoSection, KnowledgePoint, KnowledgeSummary,
│           │                        # KnowledgeMindmap, SlideOCR, ChatSession, ChatMessage
│           ├── views.py             # DRF API views
│           ├── tasks.py             # Async task implementations + TASK_REGISTRY
│           ├── agent_graph.py       # LangGraph agentic RAG implementation
│           ├── agent_tools.py       # Agent tools (search_knowledge, search_slides, …)
│           ├── rag_engine.py        # Fast RAG engine (vector retrieval)
│           ├── vector_store.py      # ChromaDB abstraction
│           ├── dashscope_asr.py     # ASR client
│           ├── lecture_video_slides_chunker.py   # SSIM slide detection
│           ├── lecture_video_hybrid_chunker.py   # Hybrid chunking
│           ├── evaluate/            # RAG evaluation module
│           │   ├── dataset_generator.py
│           │   ├── rag_modes.py     # LLM Direct / Fast RAG / Agentic RAG modes
│           │   ├── judge.py
│           │   ├── evaluator.py
│           │   └── report.py
│           └── management/commands/
│               ├── process_async_task.py   # Task processor daemon
│               ├── evaluate_rag.py         # RAG evaluation CLI
│               └── runserver.py            # Custom runserver (respects BACKEND_PORT)
│
└── frontend/
    ├── Dockerfile                   # 2-stage: node builder + nginx runtime
    ├── docker-entrypoint.sh         # writes env-config.js → starts nginx
    ├── nginx/default.conf           # SPA routing, cache headers
    ├── package.json                 # React 19, TypeScript, Ant Design 6, Tailwind
    └── src/
        ├── MainLayout.tsx           # Routing + sidebar
        ├── config.ts                # API_PREFIX from window.__ENV__ (runtime-injectable)
        ├── page/                    # Page components
        └── components/              # Reusable components (ChatPanel, lecture/*)
```

## Key Architecture Patterns

### Async Task Pipeline

The system uses a custom DAG-based task processor (`python manage.py process_async_task`):

- Tasks are stored in `AsyncTaskItem` model with `previous` field for dependency chaining
- Task functions are registered in `TASK_REGISTRY` (api/tasks.py)
- Processor polls every 5s, uses `SELECT FOR UPDATE SKIP LOCKED` for concurrency safety
- Task outputs are JSON-merged into dependent task inputs

**Current Task DAG**:
```
Upload Video
     │
     ├──→ ASR Transcription ──────────────┐
     ├──→ HLS Encoding ───────────────────┤ (parallel, no deps)
     └──→ SSIM Slide Detection ───────────┘
               │
               └──→ Thumbnail Generation  (low-res 200px for web + high-res 1920px for OCR)
                         │
                         └──→ Slide OCR   (uses high-res thumbnail when available)
                                   │
                                   └──→ Hybrid Chunking
                                             │
                                             ├──→ Fine-Grained Knowledge
                                             ├──→ Coarse-Grained Summary
                                             ├──→ Generate Mindmap
                                             └──→ Embed Knowledge
```

### RAG Modes

Three modes are implemented in `api/evaluate/rag_modes.py` and used by the chatbot:

| Mode | Description | Fallback |
|---|---|---|
| **LLM Direct** | No retrieval, pure LLM response | — |
| **Fast RAG** | Single-pass vector retrieval via ChromaDB | Falls back to LLM Direct if retrieval quality is poor |
| **Agentic RAG** | Multi-step LangGraph agent with tool calls | Falls back to Fast RAG → LLM Direct |

### Data Model Hierarchy

```
Episode (course/lecture series)
  └── Video (uploaded lecture video)
        ├── Thumbnail (slide screenshots; image=200px web, image_high_res=1920px OCR)
        ├── VideoTranscript (ASR metadata, 1:1)
        │     └── TranscriptSentence (timestamped sentences)
        ├── AsyncTaskItem (processing pipeline tasks)
        ├── SlideOCR (OCR text extracted from high-res slide images)
        ├── VideoSection (intelligent segments from hybrid chunking)
        ├── KnowledgePoint (fine-grained knowledge per section)
        ├── KnowledgeSummary (coarse-grained video-level summary)
        ├── KnowledgeMindmap (hierarchical concept map)
        └── ChatSession / ChatMessage (RAG chatbot)
```

### Key Implementation Details

- **ASR**: Uses Alibaba DashScope Qwen3-ASR; audio files uploaded to Tencent COS first
- **Slide Detection**: SSIM-based multithreaded frame comparison (`api/lecture_video_slides_chunker.py`)
- **Thumbnail Generation**: Dual-resolution — 200px (`image`) for web display, 1920px (`image_high_res`) for OCR
- **Slide OCR**: Uses `image_high_res` when available; falls back to `image`
- **Hybrid Chunking**: Combines slide transitions + silence gaps + semantic similarity (sentence-transformers)
- **Knowledge Extraction**: LLM prompts in `tasks.py` (`FINE_GRAINED_EXTRACTION_PROMPT`, `COARSE_SUMMARY_PROMPT`, `MINDMAP_PROMPT`)
- **Vector Store**: ChromaDB, path from `settings.CHROMA_PERSIST_DIR` (env: `CHROMA_PERSIST_DIR`)
- **Agentic RAG**: LangGraph state machine with tools: `search_knowledge`, `get_section_detail`, `get_transcript_range`, `search_slides`
- **Citation Sanitization**: `agent_graph.py` strips hallucinated citations from agent answers
- **Video Player**: HLS adaptive streaming with `@mux/mux-video-react`
- **Frontend API URL**: Read from `window.__ENV__.API_PREFIX` injected at container start; falls back to `http://127.0.0.1:8000`

### Settings & Configuration

All paths and ports are configurable via environment variables loaded from `.env`:

- **Database**: `DB_PATH` (default: `<BASE_DIR>/db.sqlite3`)
- **Media root**: `MEDIA_ROOT` (default: `<BASE_DIR>/media`)
- **Sub-directories**: `MEDIA_AUDIO_DIR`, `MEDIA_STREAMS_DIR`, `MEDIA_THUMBNAILS_DIR`
- **ChromaDB**: `CHROMA_PERSIST_DIR` (default: `<MEDIA_ROOT>/chromadb`)
- **Logs**: `LOG_DIR` (default: `<BASE_DIR>/logs`)
- **Backend port**: `BACKEND_PORT` (default: `8000`)
- **CORS**: `CORS_ALLOWED_ORIGINS` (default: `http://localhost:3000`)
- **Allowed hosts**: `ALLOWED_HOSTS` (default: `localhost,127.0.0.1`)

### API Endpoints

All endpoints prefixed with `/api/`:
- `GET/POST /api/videos/` — Video CRUD
- `POST /api/videos/upload/` — Multipart upload
- `GET /api/videos/<uuid>/transcript/` — ASR transcript with sentences
- `GET /api/videos/<uuid>/sections/` — Video sections/chapters
- `GET /api/tasks/video/<uuid>/` — Task status for a video
- `POST /api/chat/` — Create chat session
- `POST /api/chat/<session_id>/message/` — Send message (streaming SSE)
- `GET /api/config/` — List system configuration
- `POST /api/config/update/` — Update configuration values
- `GET /api/health/` — Health check

## Development Notes

- The async task processor must run separately from the web server for video processing to work
- FFmpeg must be installed system-wide for video/audio processing
- For low-memory systems (8GB), semantic checking in hybrid chunking is disabled (`use_semantic_check=False`)
- Task progress is tracked via `AsyncTaskItem.progress` field (0-100)
- When adding new task types: register in `TASK_REGISTRY`, implement function accepting/returning `Dict[str, Any]`
- After adding a new model field, run `python manage.py makemigrations && python manage.py migrate`
- In Docker, the `web` and `worker` services share the `lecturemind_data` volume for SQLite, media, ChromaDB, and logs
