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
- Parser/chunker CLI that converts raw documents into overlapping passages under `data/processed/` with pillar metadata.
- Embedding pipeline with pluggable writers (stdout/file/Elasticsearch-ready bulk payloads).
- In-memory retrieval service powering `/chat`, with optional DeepSeek integration when `DEEPSEEK_API_KEY` is supplied.
- Backend tests in place (pytest) plus virtualenv-friendly configuration.
- Current dataset only covers the main WAFR landing pages; full coverage will require scraping sub-sections, lenses, and PDFs before re-running the pipeline.

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
- When embeddings and a DeepSeek API key are configured the endpoint performs retrieval-augmented generation; otherwise it returns the top retrieved chunks as a preview.

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

1. Stand up Elasticsearch (local or managed), apply index mappings for text + dense vector fields, and run the embedding script (supports offline dummy vectors or real models).
2. Implement retrieval + LLM orchestration in FastAPI (`/chat`) with configurable model adapters.
3. Add Docker Compose (FastAPI + ES) and CI pipeline, then prep deployment (frontend → S3/CloudFront, backend → Lambda or container).
4. Extend ingestion to parse PDFs and capture structured metrics where available.
