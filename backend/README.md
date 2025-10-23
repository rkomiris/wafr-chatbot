# WAFR Chatbot Backend

FastAPI service that powers the AWS Well-Architected Framework chatbot. The API exposes a `/chat` endpoint for the frontend prototype and ships with a scraper that downloads Well-Architected reference content for later ingestion.

## Prerequisites

- Python 3.10+
- (Recommended) Virtual environment tool such as `python -m venv .venv`

## Installation

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Copy the environment template if you need to customise configuration:

```bash
cp .env.example .env
```

## Running the API

```bash
cd backend
uvicorn app.main:app --reload
```

The service listens on `http://localhost:8000` by default. Hit `/health` to verify the server is running.

## Running the Scraper

The scraper fetches HTML and PDF artefacts for the six pillars and the main framework page. Content is saved into `data/raw` relative to the project root by default.

```bash
cd backend
python -m app.scraper.wafr_scraper
```

To change the output directory or provide a custom specification file:

```bash
python -m app.scraper.wafr_scraper --output ../data/raw --specs-file custom_docs.json
```

The scraper emits one JSONL document per HTML source and downloads PDFs as-is. These artefacts can be uploaded to S3 and later vectorised.

## Generating Chunks for Retrieval

After scraping, normalise the documents into overlapping passages that can be embedded and indexed:

```bash
cd backend
python -m app.ingest.generate_chunks --output ../data/processed
```

Options:
- `--input`: location of raw scraper output (defaults to `../data/raw`).
- `--chunk-size`: words per chunk (default 220).
- `--overlap`: words of overlap between chunks (default 40).

The command produces `wafr_chunks.jsonl` under `data/processed/` with fields ready for Elasticsearch (chunk text, pillar metadata, summaries, etc.). PDFs are skipped until a PDF parser is added.

## Enriching Chunks with Embeddings

Generate embeddings and route them to a sink (stdout/file/Elasticsearch):

```bash
cd backend
python -m app.ingest.index_chunks --writer file
```

Common flags:
- `--embedding-model`: SentenceTransformer identifier (default `sentence-transformers/all-MiniLM-L6-v2`).
- `--writer`: `stdout`, `file`, or `elasticsearch`.
- `--output`: destination when using `file` (defaults to `../data/processed/wafr_chunks_with_embeddings.jsonl`).
- `--es-host` / `--es-index`: required when using the Elasticsearch writer.
- `--refresh-chunks`: rebuilds the processed chunks before embedding.
- `--embedding-model dummy`: deterministic offline embeddings for local smoke-tests.

The `file` writer is handy for local inspection, while the Elasticsearch writer performs a bulk index call once credentials and an endpoint are available.

## Tests

```bash
cd backend
pytest
```
