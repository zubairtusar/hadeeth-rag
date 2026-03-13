# hadeeth-rag

A local RAG chat app for searching the Holy Quran and Hadith (Bukhari & Muslim). Ask questions in natural language, get cited answers with links directly to the PDF page.

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Node.js 18+

## Setup

### 1. Environment

Copy the example env file and add your [Groq API key](https://console.groq.com) (free):

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_...
```

### 2. Backend

```bash
# Install Python dependencies
poetry install --no-root

# Start the backend (http://localhost:8000)
poetry run uvicorn backend.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 3. Frontend

> All `npm` commands must be run from inside the `frontend/` subdirectory — there is no `package.json` in the project root.

```bash
cd frontend

# Install npm dependencies (first time only)
npm install --legacy-peer-deps

# Start the dev server (http://localhost:5173)
npm run dev
```

Open `http://localhost:5173` in your browser.

## Adding PDFs

Go to **Settings** in the app to add PDF sources. Only text-layer PDFs work (you must be able to select text in a browser PDF viewer — not scanned images).

Free sources on [archive.org](https://archive.org):

| Source | Search term |
|---|---|
| Holy Quran (Arabic + English) | `Quran Saheeh International` or `Noble Quran King Fahd` |
| Sahih Bukhari | `Sahih Al-Bukhari Darussalam Arabic English` |
| Sahih Muslim | `Sahih Muslim Abdul Hamid Siddiqui` |

The embedding model (~500 MB) downloads automatically on first ingest.

## Project Structure

```
hadeeth-rag/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── api/                 # chat, sources, ingest, pdf_serve endpoints
│   ├── rag/                 # embedder, vectorstore, retriever, prompt_builder
│   ├── ingestion/           # PDF parser (Arabic RTL-aware), chunker, pipeline
│   └── models/              # schemas, source registry
├── frontend/
│   └── src/
│       ├── components/      # chat, sidebar, PDF modal, settings
│       ├── store/           # Zustand global state
│       └── api/             # fetch wrappers
├── data/
│   ├── pdfs/                # place your PDFs here
│   └── sources.json         # registered source registry
└── chroma_db/               # local vector store (auto-created)
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, Poetry |
| Vector DB | ChromaDB (local) |
| Embeddings | `intfloat/multilingual-e5-base` (Arabic + English) |
| LLM | Groq API — `llama-3.1-8b-instant` (free tier) |
| PDF parsing | PyMuPDF |
| Frontend | React 19, Vite, TypeScript, Tailwind CSS |
| State | Zustand |
| PDF viewer | react-pdf |
