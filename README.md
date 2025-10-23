# WAFR Chatbot

Prototype implementation of a Well-Architected Framework assistant. The project currently ships a polished chat UI and a FastAPI backend scaffold with a document scraper. Retrieval, embeddings, and LLM orchestration can be added in subsequent iterations.

## Repository Structure

```
.
├── backend/            # FastAPI service + scraper utilities
├── data/raw/           # Local store for scraped documents
├── frontend/           # React + Vite + Tailwind chat experience
└── README.md
```

## Current Progress

- React + Vite + Tailwind UI with conversation history, pillar prompts, and API integration.
- FastAPI backend exposing `/health` and `/chat` with a placeholder response service and CORS configured for localhost/127.0.0.1.
- Python scraper that gathers core AWS Well-Architected HTML content into `data/raw/` (PDF fetch currently blocked by AWS 403).
- Backend tests in place (pytest) plus virtualenv-friendly configuration.

## Frontend (React + Vite + Tailwind)

The frontend provides a responsive chat workspace with hero messaging, conversation history, and contextual prompts for the six AWS Well-Architected pillars.

### Getting Started

```bash
cd frontend
npm install
npm run dev
```

Environment variables:

- `VITE_API_BASE_URL` (optional): defaults to `http://localhost:8000`. Point to the FastAPI instance you want to consume.

## Backend (FastAPI)

The FastAPI application currently offers:

- `GET /health` – simple heartbeat.
- `POST /chat` – echoes user questions using a placeholder service (LLM integration to follow).

Run the backend locally:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

See `backend/README.md` for more details and for scraper instructions.

## Scraper

The scraper (`python -m app.scraper.wafr_scraper`) downloads HTML and PDF artefacts covering the core Well-Architected content. Files are persisted to `data/raw` for later ingest and S3 upload.

## Suggested Next Steps

1. Build a parser/chunker that converts `data/raw/` assets into cleaned passages with metadata (pillar, section, metrics).
2. Generate embeddings for each chunk (e.g., SentenceTransformers) and design the Elasticsearch index mappings (text + dense vectors).
3. Implement retrieval + LLM flow in FastAPI (`/chat`) with configurable model adapters.
4. Add Docker Compose (FastAPI + ES) and CI pipeline, then prep deployment (frontend → S3/CloudFront, backend → Lambda or container).
