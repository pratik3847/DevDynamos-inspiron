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
flowchart LR
  subgraph Frontend["Frontend Layer (Vite + React)"]
    UI_Dashboard["Dashboard<br/>Session List<br/>Upload Interface"]
    UI_Upload["File Upload<br/>Drag & Drop<br/>Multi-file Support"]
    UI_Validation["Validation View<br/>Error Display<br/>Warning Filters"]
    UI_Fixer["Fix Assistant<br/>Apply/Batch Fixes<br/>Preview Changes"]
    UI_835["835 Dashboard<br/>Payment Summary<br/>Claim Details"]
    UI_Rules["Rules Manager<br/>Enable/Disable<br/>Custom Preferences"]
    UI_Chat["Eddie Chat<br/>AI Assistant<br/>Context-Aware Help"]
  end

  subgraph API_Layer["API Layer (FastAPI)"]
    Auth_Service["Auth Service<br/>JWT Tokens<br/>User Sessions<br/>Signup/Login"]
    File_Router["File Router<br/>Upload Handler<br/>Session Manager<br/>Download Service"]
    Fix_Router["Fix Router<br/>Apply Fixes<br/>Batch Processing<br/>Validation Trigger"]
    Rules_Router["Rules Router<br/>CRUD Operations<br/>Default Reset<br/>User Preferences"]
    AI_Router["AI Router<br/>Question Handler<br/>Segment Explainer<br/>Error Analyzer"]
    Parser_Router["835 Parser Router<br/>Upload 835<br/>Parse & Analyze<br/>Pattern Detection"]
  end

  subgraph Processing["Processing Engine"]
    Parser_Main["Parser Service<br/>pyx12 Engine<br/>Fallback Parser<br/>Segment Tokenizer"]
    Parser_Agent["Parser Agent<br/>RAG Enrichment<br/>Context Builder<br/>TR3 Lookup"]
    
    subgraph Validation_Layer["Validation Engine"]
      Val_Structural["Structural Validator<br/>Segment Order<br/>Required Elements<br/>Data Types"]
      Val_Business["Business Rules<br/>837/835/834 Logic<br/>Cross-Segment<br/>Amount Checks"]
      Val_External["External Validator<br/>Code Lists<br/>TR3 Reference<br/>CMS Guidelines"]
    end
    
    Val_Filter["Rule Filter<br/>Apply User Rules<br/>Severity Mapping<br/>Error Deduplication"]
    
    subgraph Fix_Engine["Fix Agent Engine"]
      Fix_Deterministic["Deterministic Fixer<br/>Control Numbers<br/>Envelope Counts<br/>Calculated Fields"]
      Fix_RAG["RAG-Enhanced Fixer<br/>TR3 Citations<br/>Best Practices<br/>Context Suggestions"]
      Fix_Validator["Fix Validator<br/>Pre-Apply Check<br/>Impact Analysis<br/>Conflict Detection"]
    end
    
    Report_Builder["Report Builder<br/>PDF Generator<br/>JSON MD HTML<br/>Change History<br/>Fix Summary"]
  end

  subgraph Data_Layer["Data Layer"]
    MongoDB["MongoDB<br/>Collections:"]
    DB_Users[("users<br/>Auth Data<br/>Credentials<br/>Preferences")]
    DB_Sessions[("sessions<br/>Upload History<br/>Parsed JSON<br/>Validation State<br/>Fix Reports")]
    DB_Rules[("rules<br/>User Rules<br/>Enabled/Disabled<br/>Custom Configs")]
    MongoDB -.-> DB_Users
    MongoDB -.-> DB_Sessions
    MongoDB -.-> DB_Rules
  end

  subgraph AI_Layer["AI & RAG Layer"]
    Qdrant["Qdrant Vector DB<br/>240,054 Embeddings<br/>Similarity: 0.3 threshold"]
    Embeddings["Sentence Transformers<br/>all-MiniLM-L6-v2<br/>384-dim vectors"]
    
    subgraph RAG_Sources["Knowledge Sources"]
      RAG_TR3["TR3 Guides<br/>837/835/834<br/>Segment Specs<br/>Loop Structure"]
      RAG_CMS["CMS Manuals<br/>Guidelines<br/>Compliance Rules<br/>Best Practices"]
      RAG_Codes["Code Lists<br/>CARC/RARC<br/>Adjustment Codes<br/>Remark Codes"]
    end
    
    Groq["Groq LLM<br/>Low Latency<br/>Context Window<br/>Auto Model Select"]
    RAG_Sources --> Embeddings
    Embeddings --> Qdrant
  end

  Frontend --> API_Layer
  UI_Dashboard -->|POST /files/upload<br/>GET /files/sessions| File_Router
  UI_Upload -->|Multipart Form<br/>EDI File Payload| File_Router
  UI_Validation -->|GET /session/ID<br/>Filter Params| File_Router
  UI_Fixer -->|POST /fix/apply<br/>POST /fix/apply-batch| Fix_Router
  UI_835 -->|GET /835-dashboard<br/>Payment Summary| Parser_Router
  UI_Rules -->|GET PUT /rules<br/>POST /rules/reset| Rules_Router
  UI_Chat -->|POST /api/ai/eddie-chat<br/>Context History| AI_Router
  UI_Dashboard -->|POST /auth/login<br/>POST /auth/signup| Auth_Service
  
  Auth_Service -->|JWT Token<br/>User Context| DB_Users
  File_Router -->|Raw EDI<br/>File Metadata| Parser_Main
  Parser_Main -->|Segment List<br/>Loop Hierarchy| Parser_Agent
  Parser_Agent -->|Enriched Context<br/>TR3 References| Qdrant
  Parser_Agent -->|Normalized JSON<br/>Segment Hierarchy| Val_Structural
  
  Val_Structural -->|Structural Results<br/>Element Errors| Val_Business
  Val_Business -->|Business Results<br/>Logic Errors| Val_External
  Val_External -->|External Results<br/>Code Errors| Val_Filter
  Val_Filter -->|Query User Rules<br/>Enabled/Disabled| Rules_Router
  Rules_Router <-->|CRUD Operations<br/>Default Sets| DB_Rules
  Val_External -->|Code Lookup<br/>TR3 Validation| Qdrant
  
  Val_Filter -->|Filtered Errors<br/>Prioritized List| Fix_Deterministic
  Fix_Deterministic -->|Concrete Fixes<br/>Calculated Values| Fix_RAG
  Fix_RAG -->|RAG Context<br/>TR3 Citations| Qdrant
  Fix_RAG -->|Enhanced Suggestions<br/>Reasoning| Fix_Validator
  Fix_Router -->|Apply Fix Request<br/>Session ID + Fix| Fix_Validator
  Fix_Validator -->|Validated Fix<br/>Impact Report| Parser_Main
  Parser_Main -->|Regenerated EDI<br/>Modified JSON| Val_Structural
  
  Fix_Validator -->|Fix History<br/>Change Log| Report_Builder
  Report_Builder -->|PDF JSON MD HTML<br/>Download URL| File_Router
  File_Router <-->|Save/Load Sessions<br/>Upload State| DB_Sessions
  Fix_Router <-->|Update Session<br/>Fix Reports| DB_Sessions
  Parser_Agent <-->|Store Results<br/>Parsed Data| DB_Sessions
  
  AI_Router -->|Question Context<br/>Session Data| Groq
  AI_Router -->|RAG Query<br/>Similarity Search| Qdrant
  Groq -->|LLM Response<br/>Explanation| AI_Router
  Parser_Router -->|835 Parse Request<br/>File Content| Parser_Main
  Parser_Router -->|Pattern Analysis<br/>Claim Aggregation| Qdrant
  Parser_Router <-->|In-Memory Store<br/>Demo Mode| DB_Sessions
  UI_Validation -->|User Feedback<br/>Issue Report| AI_Router
  Report_Builder -->|Audit Trail<br/>Compliance Report| DB_Sessions
  Val_Filter -->|Statistics<br/>Error Trends| UI_Dashboard

  classDef frontendStyle fill:#e1f5ff,stroke:#01579b,stroke-width:3px,color:#000,font-size:16px
  classDef apiStyle fill:#fff3e0,stroke:#e65100,stroke-width:3px,color:#000,font-size:16px
  classDef processStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:3px,color:#000,font-size:16px
  classDef dataStyle fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px,color:#000,font-size:16px
  classDef aiStyle fill:#fce4ec,stroke:#880e4f,stroke-width:3px,color:#000,font-size:16px
  
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
