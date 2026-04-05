# RAG Knowledge Service

## Overview

This service provides semantic search over **240,054 embeddings** of HIPAA EDI documentation, enabling agents to retrieve relevant information for validation, fix suggestions, and explanations.

## 📚 Knowledge Base Contents

- **TR3 Implementation Guides:** 834, 835, 837I, 837P (155 pages)
- **CMS Claims Processing Manual:** Chapter 25 (30 pages)
- **Code Lists:** 74K+ ICD-10 codes, CARC, RARC, POS codes
- **Vector Database:** Qdrant Cloud
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2

## 🚀 Quick Start

### Basic Usage

```python
from app.services.rag import RAGClient

# Initialize client
rag = RAGClient()

# Ask a question
results = rag.query("What segments are required in Loop 2310B for 837P?")

# Process results
for result in results:
    print(f"Source: {result['source_doc']} (page {result['page']})")
    print(f"Content: {result['text']}")
    print(f"Relevance: {result['score']:.2%}")
```

## 📖 Integration Examples

### 1. Validator Agent Integration

```python
# backend/app/services/agents/validator_agent.py
from app.services.rag import RAGClient

class ValidatorAgent:
    def __init__(self):
        self.rag = RAGClient()
    
    def validate_837p(self, edi_data: dict):
        # Query RAG for validation rules
        loop_requirements = self.rag.query(
            "What are the required segments in Loop 2310B for 837P professional claims?",
            transaction_type="837P",
            top_k=3
        )
        
        # Extract rules from RAG results
        required_segments = self._extract_required_segments(loop_requirements)
        
        # Validate against actual data
        errors = []
        for segment in required_segments:
            if segment not in edi_data['loops']['2310B']:
                errors.append({
                    "error": f"Missing required segment: {segment}",
                    "loop": "2310B",
                    "source": loop_requirements[0]['source_doc']
                })
        
        return errors
```

### 2. Fix Suggestion Agent Integration

```python
# backend/app/services/agents/fix_agent.py
from app.services.rag import RAGClient

class FixAgent:
    def __init__(self):
        self.rag = RAGClient()
    
    def suggest_fix(self, error: dict):
        # Query RAG for fix guidance
        segment_info = self.rag.query(
            f"How to add {error['segment']} segment in {error['loop']} for {error['transaction_type']}?",
            transaction_type=error['transaction_type'],
            top_k=3
        )
        
        # Generate fix instructions
        fix_suggestion = {
            "error_code": error['error_code'],
            "fix_steps": [
                f"Add {error['segment']} segment to Loop {error['loop']}",
                "Ensure NPI identifier is present",
                "Verify segment order matches TR3 specification"
            ],
            "code_example": self._generate_code_example(segment_info),
            "documentation": segment_info[0]['source_doc'],
            "page_reference": segment_info[0]['page']
        }
        
        return fix_suggestion
```

### 3. Explainer Agent Integration

```python
# backend/app/services/agents/explainer_agent.py
from app.services.rag import RAGClient

class ExplainerAgent:
    def __init__(self):
        self.rag = RAGClient()
    
    def explain_error(self, error: dict):
        # Query RAG for regulatory context
        context = self.rag.query(
            f"Why is {error['segment']} required in {error['loop']} for {error['transaction_type']}?",
            transaction_type=error['transaction_type'],
            doc_type="tr3",
            top_k=2
        )
        
        # Also check CMS manual
        cms_context = self.rag.search_claims_manual(
            f"What are the requirements for {error['segment']} in professional claims?"
        )
        
        explanation = {
            "plain_language": f"This error occurs because {error['transaction_type']} claims require {error['segment']} segment to identify the rendering provider.",
            "regulatory_context": context[0]['text'],
            "cms_guidance": cms_context[0]['text'] if cms_context else None,
            "impact": "Claim will be rejected by the payer without this information.",
            "citations": [
                f"{context[0]['source_doc']} (page {context[0]['page']})",
                f"{cms_context[0]['source_doc']} (page {cms_context[0]['page']})" if cms_context else None
            ]
        }
        
        return explanation
```

### 4. Parser Agent Integration

```python
# backend/app/services/agents/parser_agent.py
from app.services.rag import RAGClient

class ParserAgent:
    def __init__(self):
        self.rag = RAGClient()
    
    def parse_segment(self, segment_code: str, transaction_type: str):
        # Query RAG for segment definition
        segment_info = self.rag.query(
            f"What is the structure of {segment_code} segment in {transaction_type}?",
            transaction_type=transaction_type,
            top_k=2
        )
        
        # Extract segment structure
        structure = {
            "segment_code": segment_code,
            "elements": self._extract_elements(segment_info),
            "definition": segment_info[0]['text'],
            "source": segment_info[0]['source_doc']
        }
        
        return structure
```

## 🔍 API Reference

### RAGClient Methods

#### `query(question, top_k, transaction_type, doc_type, min_score)`
Main query method for natural language questions.

**Parameters:**
- `question` (str): Natural language question
- `top_k` (int, optional): Number of results (default: 5, max: 20)
- `transaction_type` (str, optional): Filter by 834, 835, 837I, 837P
- `doc_type` (str, optional): Filter by tr3, claims_manual, code_list
- `min_score` (float, optional): Minimum similarity (default: 0.7)

**Returns:** List of dictionaries with:
- `text`: Document content
- `source_doc`: Source document name
- `page`: Page number
- `score`: Similarity score (0-1)
- `doc_type`: Document type
- `transaction_type`: Transaction type
- `metadata`: Full metadata

#### `search_by_transaction(question, transaction_type, top_k)`
Search within specific transaction type.

#### `search_tr3_guides(question, top_k)`
Search only TR3 implementation guides.

#### `search_claims_manual(question, top_k)`
Search only CMS Claims Processing Manual.

#### `search_code_lists(code, top_k)`
Search medical codes (ICD-10, CARC, RARC, POS).

#### `get_stats()`
Get knowledge base statistics.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory with:

```env
# Qdrant Configuration
QDRANT_HOST=your-qdrant-host.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=your-api-key-here
QDRANT_COLLECTION_NAME=edi_knowledge

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

**Note:** A template `.env.rag` file is provided with the current configuration.

### RAG Service Config

Edit `backend/app/services/rag/config.py` to adjust:
- `DEFAULT_TOP_K`: Default number of results (5)
- `MAX_TOP_K`: Maximum allowed results (20)
- `SIMILARITY_THRESHOLD`: Minimum similarity score (0.7)

## 📊 Knowledge Base Statistics

```python
rag = RAGClient()
stats = rag.get_stats()
print(f"Total embeddings: {stats['vectors_count']:,}")
print(f"Collection status: {stats['status']}")
```

## 🧪 Testing

```python
# Test connection
from app.services.rag import RAGClient

rag = RAGClient()

# Simple query test
results = rag.query("What is Loop 2310B?")
assert len(results) > 0
print(f"✓ Found {len(results)} results")

# Transaction-specific test
results = rag.search_by_transaction("Required segments", "837P")
assert all(r['transaction_type'] == '837P' for r in results)
print(f"✓ Transaction filter working")

# Code lookup test
results = rag.search_code_lists("A00.0")
print(f"✓ ICD-10 code lookup: {results[0]['text']}")
```

## 📈 Performance

- **Average query time:** ~100-200ms
- **Embedding generation:** ~50ms per query
- **Qdrant search:** ~50-150ms
- **Total vectors:** 240,054 embeddings
- **Collection size:** ~92 MB

## 🔄 Adding New Documentation

To add new documents to the knowledge base:

1. Place PDFs in your RAG system's `edi-docs/` folder
2. Run the embedding script (contact RAG system owner)
3. New embeddings are automatically available to all agents

## 🛠️ Troubleshooting

### Connection Issues

```python
rag = RAGClient()
# If you see: "⚠ RAG Client initialized but collection not accessible"
# Check: .env file exists and has correct credentials
```

### Empty Results

```python
results = rag.query("your question", min_score=0.5)  # Lower threshold
results = rag.query("your question", top_k=10)        # More results
```

### Slow Queries

```python
# Use filters to narrow search space
results = rag.query(
    "your question",
    transaction_type="837P",  # Reduces search space
    doc_type="tr3"            # Searches only TR3 guides
)
```

## 📞 Support

For RAG system issues, questions, or documentation requests, contact the RAG system owner.

## 📝 License

Internal use only - HIPAA EDI documentation is subject to CMS and X12 licensing.
