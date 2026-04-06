# EDI Platform

End to end EDI parsing, validation, fixing, and RAG powered explanation for US healthcare transactions (837P, 835, 834).

## Contents
- Frontend: Vite + React UI (dashboard, upload, validation, fix assistant)
- Backend: FastAPI services with MongoDB persistence
- Validation engine: Structural, business, and external layers
- RAG knowledge base: Qdrant + sentence transformers for TR3 and code lookups
- AI assistant: Groq backed explainer endpoints
- Reporting: PDF, JSON, Markdown, and HTML fix reports

## Tech stack (short rationale)
- Vite + React: fast dev server and simple SPA routing for the dashboard.
- FastAPI: lightweight, typed Python APIs with async support.
- MongoDB: flexible JSON documents for session and rules data.
- pyx12: mature X12 parsing for reliable segment extraction.
- Qdrant + sentence-transformers: vector search over TR3 and code lists for RAG.
- Groq LLM: low latency responses for explainers and chat.
- ReportLab: stable PDF generation for fix reports.

## Architecture at a glance

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'background':'#ffffff', 'mainBkg':'#ffffff', 'clusterBkg':'#ffffff', 'fontSize':'22px'}}}%%
flowchart LR
  subgraph Frontend["<b>Frontend Layer</b>"]
    UI_Dashboard["<b>Dashboard</b><br/>Session List | Upload Interface"]
    UI_Upload["<b>File Upload</b><br/>Drag Drop | Multi-file Support"]
    UI_Validation["<b>Validation View</b><br/>Error Display | Warning Filters"]
    UI_Fixer["<b>Fix Assistant</b><br/>Apply Batch Fixes | Preview Changes"]
    UI_835["<b>835 Dashboard</b><br/>Payment Summary | Claim Details"]
    UI_Rules["<b>Rules Manager</b><br/>Enable Disable | Custom Preferences"]
    UI_Chat["<b>Eddie Chat</b><br/>AI Assistant | Context-Aware Help"]
  end

  subgraph API_Layer["<b>API Layer</b>"]
    Auth_Service["<b>Auth Service</b><br/>JWT Tokens | User Sessions | Signup Login"]
    File_Router["<b>File Router</b><br/>Upload Handler | Session Manager | Download Service"]
    Fix_Router["<b>Fix Router</b><br/>Apply Fixes | Batch Processing | Validation Trigger"]
    Rules_Router["<b>Rules Router</b><br/>CRUD Operations | Default Reset | User Preferences"]
    AI_Router["<b>AI Router</b><br/>Question Handler | Segment Explainer | Error Analyzer"]
    Parser_Router["<b>835 Parser Router</b><br/>Upload 835 | Parse Analyze | Pattern Detection"]
  end

  subgraph Processing["<b>Processing Engine</b>"]
    Parser_Main["<b>Parser Service</b><br/>pyx12 Engine | Fallback Parser | Segment Tokenizer"]
    Parser_Agent["<b>Parser Agent</b><br/>RAG Enrichment | Context Builder | TR3 Lookup"]
    Val_Structural["<b>Structural Validator</b><br/>Segment Order | Required Elements | Data Types"]
    Val_Business["<b>Business Rules</b><br/>837 835 834 Logic | Cross-Segment | Amount Checks"]
    Val_External["<b>External Validator</b><br/>Code Lists | TR3 Reference | CMS Guidelines"]
    Val_Filter["<b>Rule Filter</b><br/>Apply User Rules | Severity Mapping | Error Deduplication"]
    Fix_Deterministic["<b>Deterministic Fixer</b><br/>Control Numbers | Envelope Counts | Calculated Fields"]
    Fix_RAG["<b>RAG-Enhanced Fixer</b><br/>TR3 Citations | Best Practices | Context Suggestions"]
    Fix_Validator["<b>Fix Validator</b><br/>Pre-Apply Check | Impact Analysis | Conflict Detection"]
    Report_Builder["<b>Report Builder</b><br/>PDF Generator | JSON MD HTML | Change History | Fix Summary"]
  end

  subgraph Data_Layer["<b>Data Layer</b>"]
    MongoDB["<b>MongoDB Collections</b>"]
    DB_Users[("<b>users</b><br/>Auth Data | Credentials | Preferences")]
    DB_Sessions[("<b>sessions</b><br/>Upload History | Parsed JSON | Validation State | Fix Reports")]
    DB_Rules[("<b>rules</b><br/>User Rules | Enabled Disabled | Custom Configs")]
    MongoDB -.-> DB_Users
    MongoDB -.-> DB_Sessions
    MongoDB -.-> DB_Rules
  end

  subgraph AI_Layer["<b>AI & RAG Layer</b>"]
    Qdrant["<b>Qdrant Vector DB</b><br/>240054 Embeddings | Similarity 0.3 threshold"]
    Embeddings["<b>Sentence Transformers</b><br/>all-MiniLM-L6-v2 | 384-dim vectors"]
    RAG_TR3["<b>TR3 Guides</b><br/>837 835 834 | Segment Specs | Loop Structure"]
    RAG_CMS["<b>CMS Manuals</b><br/>Guidelines | Compliance Rules | Best Practices"]
    RAG_Codes["<b>Code Lists</b><br/>CARC RARC | Adjustment Codes | Remark Codes"]
    Groq["<b>Groq LLM</b><br/>Low Latency | Context Window | Auto Model Select"]
    RAG_TR3 --> Embeddings
    RAG_CMS --> Embeddings
    RAG_Codes --> Embeddings
    Embeddings --> Qdrant
  end

  Frontend --> API_Layer
  UI_Dashboard --> File_Router
  UI_Upload --> File_Router
  UI_Validation --> File_Router
  UI_Fixer --> Fix_Router
  UI_835 --> Parser_Router
  UI_Rules --> Rules_Router
  UI_Chat --> AI_Router
  UI_Dashboard --> Auth_Service
  Auth_Service --> DB_Users
  File_Router --> Parser_Main
  Parser_Main --> Parser_Agent
  Parser_Agent --> Qdrant
  Parser_Agent --> Val_Structural
  Val_Structural --> Val_Business
  Val_Business --> Val_External
  Val_External --> Val_Filter
  Val_Filter --> Rules_Router
  Rules_Router --> DB_Rules
  Val_External --> Qdrant
  Val_Filter --> Fix_Deterministic
  Fix_Deterministic --> Fix_RAG
  Fix_RAG --> Qdrant
  Fix_RAG --> Fix_Validator
  Fix_Router --> Fix_Validator
  Fix_Validator --> Parser_Main
  Parser_Main --> Val_Structural
  Fix_Validator --> Report_Builder
  Report_Builder --> File_Router
  File_Router --> DB_Sessions
  Fix_Router --> DB_Sessions
  Parser_Agent --> DB_Sessions
  AI_Router --> Groq
  AI_Router --> Qdrant
  Groq --> AI_Router
  Parser_Router --> Parser_Main
  Parser_Router --> Qdrant
  Parser_Router --> DB_Sessions
  UI_Validation --> AI_Router
  Report_Builder --> DB_Sessions
  Val_Filter --> UI_Dashboard

  classDef frontendStyle fill:#ffffff,stroke:#0066cc,stroke-width:4px,color:#000000,font-size:22px,font-weight:bold
  classDef apiStyle fill:#ffffff,stroke:#ff6600,stroke-width:4px,color:#000000,font-size:22px,font-weight:bold
  classDef processStyle fill:#ffffff,stroke:#6600cc,stroke-width:4px,color:#000000,font-size:22px,font-weight:bold
  classDef dataStyle fill:#ffffff,stroke:#009933,stroke-width:4px,color:#000000,font-size:22px,font-weight:bold
  classDef aiStyle fill:#ffffff,stroke:#cc0066,stroke-width:4px,color:#000000,font-size:22px,font-weight:bold
  
  class UI_Dashboard,UI_Upload,UI_Validation,UI_Fixer,UI_835,UI_Rules,UI_Chat frontendStyle
  class Auth_Service,File_Router,Fix_Router,Rules_Router,AI_Router,Parser_Router apiStyle
  class Parser_Main,Parser_Agent,Val_Structural,Val_Business,Val_External,Val_Filter,Fix_Deterministic,Fix_RAG,Fix_Validator,Report_Builder processStyle
  class MongoDB,DB_Users,DB_Sessions,DB_Rules dataStyle
  class Qdrant,Embeddings,RAG_TR3,RAG_CMS,RAG_Codes,Groq aiStyle
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
