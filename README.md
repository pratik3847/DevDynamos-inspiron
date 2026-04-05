# EDI Platform

End to end EDI parsing, validation, fixing, and RAG powered explanation for US healthcare transactions (837P, 835, 834).

## Contents
- Frontend: Vite + React UI (dashboard, upload, validation, fix assistant)
- Backend: FastAPI services with MongoDB persistence
- Validation engine: Structural, business, and external layers
- RAG knowledge base: Qdrant + sentence transformers for TR3 and code lookups
- AI assistant: Groq backed explainer endpoints
- Reporting: PDF, JSON, Markdown, and HTML fix reports

## Architecture at a glance

```mermaid
flowchart LR
  FE[Vite + React UI]
  API[FastAPI API]
  DB[(MongoDB)]
  Parser[Parser (pyx12)]
  Validator[Validation Engine]
  Fixer[Fix Agent]
  Rules[Rules Service]
  Reports[Report Builder]
  RAG[(Qdrant)]
  Embeddings[Embedding Model]
  LLM[Groq LLM]

  FE -->|/auth /files /fix /rules /api| API
  API --> Parser
  Parser --> Validator
  Validator --> Fixer
  Validator --> Rules
  Fixer --> Reports
  API --> DB
  Rules --> DB
  Validator --> RAG
  Fixer --> RAG
  API --> LLM
  RAG --> Embeddings
```

## Core workflows

### Upload and validate
1. UI uploads an EDI file to `POST /files/upload`.
2. Backend parses EDI with pyx12 into a normalized segment list.
3. Validation runs across three layers (structural, business, external).
4. Rule preferences filter which validation issues are shown.
5. Fix agent generates deterministic suggestions when a concrete value can be derived.
6. A session document is persisted to MongoDB.

### Apply fixes
1. UI applies a single fix via `POST /fix/apply` or a batch via `POST /fix/apply-batch`.
2. Backend updates `modifiedJson`, regenerates EDI, and revalidates.
3. A fix report entry is appended, and remaining issues are recomputed.
4. The session status is updated to `Clean` or `Requires Attention`.

### 835 remittance tools
The 835 parser routes under `/api/parser` provide dedicated endpoints for upload, parsing, payment summaries, claim details, and RAG powered code explanations. Uploaded 835 files are stored in memory for demo use and reset on restart.

## Key components

### Parser
- Uses pyx12 to tokenize EDI segments.
- Falls back to manual parsing on errors or timeouts.
- Optional RAG enrichment of parsed segments via `ParserAgent`.

### Validation engine
- Three layers: structural, business, external.
- Collects all errors and warnings instead of failing fast.
- Supports transaction specific rules for 837, 835, and 834.

### Fix agent
- Generates deterministic fixes for envelope counts and control numbers.
- Avoids placeholder fixes when a concrete value cannot be derived.
- Best effort RAG enrichment adds TR3 citations to fix reasoning.

### Rules service
- Per user rule sets stored in MongoDB.
- Disabling a rule filters issues by code or rule id; it does not change validator logic.

### RAG knowledge base
- Qdrant vector database with 240,054 embeddings.
- Sources include TR3 guides, CMS manuals, and code lists.
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`.
- Default similarity threshold is `0.3` for broader recall.

### AI assistant
- Groq backed LLM for explainers, error analysis, and Eddie chat.
- Segment explanations use RAG context when available.

## Data model (MongoDB)

### Collections
- `users`: authentication records
- `sessions`: upload, parsing, validation, fixes, and report history
- `rules`: per user rule preferences

### Session highlights
- `rawEdi`, `parsedJson`, `modifiedJson`, `correctedEdi`
- `validationErrors` (current) and `originalValidationErrors` (unchanged)
- `fixes`, `fixReports`, `changesLog`
- `memberEnrollmentSummary`

## API overview

### Auth
- `POST /auth/signup`
- `POST /auth/login`

### Files and sessions (auth required)
- `POST /files/upload`
- `GET /files/sessions`
- `GET /files/session/{session_id}`
- `DELETE /files/session/{session_id}`
- `GET /files/session/{session_id}/835-dashboard`
- `GET /files/session/{session_id}/download/edi`
- `GET /files/session/{session_id}/download/json`
- `GET /files/session/{session_id}/download/report?format=pdf|json|md|html`

### Fixes (auth required)
- `POST /fix/apply`
- `POST /fix/apply-batch`

### Rules (auth required)
- `GET /rules`
- `PUT /rules`
- `POST /rules/reset`

### AI assistant
- `POST /api/ai/ask-question`
- `POST /api/ai/explain-segment`
- `POST /api/ai/analyze-error`
- `POST /api/ai/suggest-fixes`
- `POST /api/ai/chat`
- `POST /api/ai/eddie-chat`
- `GET /api/ai/health`

### 835 parser (auth required)
- `POST /api/parser/upload-835`
- `POST /api/parser/parse/{file_id}`
- `GET /api/parser/payment-summary/{file_id}`
- `GET /api/parser/claim-details/{file_id}`
- `POST /api/parser/explain-adjustment`
- `POST /api/parser/analyze-patterns/{file_id}`
- `POST /api/parser/ask-question/{file_id}`
- `GET /api/parser/files`

## Configuration

### Backend environment variables
Create `backend/.env` and set what you need:

```
GROQ_API_KEY=...
GROQ_MODEL=auto
MONGODB_URI=mongodb://localhost:27017
JWT_SECRET=dev-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=60

QDRANT_HOST=your-qdrant-host
QDRANT_PORT=6333
QDRANT_API_KEY=your-api-key
QDRANT_COLLECTION_NAME=edi_knowledge
```

### RAG configuration
Defaults live in `backend/app/services/rag/config.py`:
- `DEFAULT_TOP_K=5`
- `MAX_TOP_K=20`
- `SIMILARITY_THRESHOLD=0.3`

## Local development

### Backend
```
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```
npm install
npm run dev
```

### Workspace sanity check (Windows)
```
./scripts/workspace-sanity.ps1
```

## Ports and proxy
- Backend: http://localhost:8000
- Frontend: http://localhost:5173 (Vite will use 5174 if 5173 is taken)
- Vite proxy routes: `/api`, `/auth`, `/files`, `/fix`, `/rules`

## Notes and limitations
- The 835 parser uses in memory storage for demo use; data is not persisted across restarts.
- RAG and LLM features are optional. If Qdrant or Groq is not configured, the backend still runs but AI responses may be limited.

## Additional docs
- Backend architecture: `backend/README.md`
- RAG service details: `backend/app/services/rag/README.md`
- Validation engine: `backend/app/services/validation/README.md`
- Ports and commands: `docs/ports.md`
