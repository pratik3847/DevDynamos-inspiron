# Ports + dev commands

## Backend (FastAPI)
- **Working directory**: `backend/`
- **Base URL**: `http://localhost:8000`
- **Start (venv python, explicit)**:
  - `d:/edistarttoend/edi/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000`
- **Start (if venv activated)**:
  - `uvicorn app.main:app --reload --port 8000`

## Database (MongoDB)
- **Env var**: `MONGODB_URI`
  - Default if unset: `mongodb://localhost:27017`
  - Set in `backend/.env` (loaded via `python-dotenv`)
- **Optional env var**: `DATABASE_NAME`
  - Default if unset: `edi_platform`

## Frontend (Vite + React)
- **Working directory**: repo root
- **Dev server**: typically `http://localhost:5173` (Vite will use `5174` if `5173` is taken)
- **Start**: `npm run dev`

## Dev proxy (Vite → backend)
Configured in `vite.config.ts`:
- `/api` → `http://localhost:8000`
- `/auth` → `http://localhost:8000`
- `/files` → `http://localhost:8000`
- `/fix` → `http://localhost:8000`

## Notes
- Backend CORS currently allows: `http://localhost:5173`, `http://localhost:5174`, `http://localhost:3000`.
- To re-check everything quickly, run: `./scripts/workspace-sanity.ps1`.
