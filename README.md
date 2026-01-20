# AI Blog Writer Monorepo

An Nx-managed monorepo that turns CSV video metadata into a multi-stage AI
pipeline, producing a Markdown article with provenance-aware citations.

<h2 style="margin-bottom: 0.5rem;">Frontend (apps/frontend):</h2>
<p>
<img alt="TypeScript" src="https://img.shields.io/badge/typescript-007ACC?style=for-the-badge&logo=typescript&logoColor=white"/>
 <img alt="React" src="https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB"/>
 <img alt="CSS" src="https://img.shields.io/badge/css-%231572B6.svg?style=for-the-badge&logo=css&logoColor=white"/>

</p>
<h2 style="margin-bottom: 0.5rem;">Backend (apps/backend):</h2>
<p>
<img alt="Python" src="https://img.shields.io/badge/Python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54"/>
<img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img alt="SQLite" src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white"/>

</p>

<h2>AI Integration – Content Processing</h2>
<p>
<img alt="Vertex AI" src="https://img.shields.io/badge/Vertex%20AI-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white"/>
</p>


## Workspace layout

```
apps/frontend     # Vite + React + TanStack Query SPA
apps/backend      # FastAPI service (Python 3.11)
packages/shared   # Pydantic schemas and shared types
packages/utils    # CSV parsing, normalization, chunking, Weaviate helpers
output            # Generated Markdown + aggregated artifact JSON
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker + Docker Compose (optional)

## Setup

```bash
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r apps/backend/requirements.txt -r apps/backend/requirements-dev.txt
```

Copy environment files:

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env
```

**Important**: Edit `apps/backend/.env` and set your actual Google Cloud Project ID:

```bash
GOOGLE_CLOUD_PROJECT=your-actual-gcp-project-id
```

You also need to authenticate with Google Cloud:

```bash
gcloud auth application-default login
```

## Development

```bash
npx nx serve backend
npx nx serve frontend
```

Frontend runs on `http://localhost:5173` and backend on `http://localhost:8000`.

## Docker

```bash
docker compose up --build
```

This starts:
- FastAPI backend (`:8000`)
- Vite frontend (`:5173`)
- Weaviate (`:8080`)

## Upload a CSV

```bash
curl -F "file=@/path/to/your.csv" http://localhost:8000/upload
```

Then poll:

```bash
curl http://localhost:8000/status/<run_id>
```

Fetch results:

```bash
curl http://localhost:8000/result/<run_id>
curl http://localhost:8000/result/<run_id>?format=md
```

Markdown output is saved to `output/<run_id>.md` and the aggregated artifact is
stored at `output/<run_id>/video_artifact.json`.

## Nx tasks

```bash
npx nx lint frontend
npx nx test backend
npx nx build frontend
npx nx docker-build backend
```

Python targets are configured through Nx with the `@nxlv/python` plugin (plus
run-commands for local tooling).

## Notes

- Stage outputs are stored under `data/runs/<run_id>/`.