"""RAG service configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "edi_knowledge")

# Embedding model
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Search configuration
DEFAULT_TOP_K = 5
MAX_TOP_K = 20
SIMILARITY_THRESHOLD = 0.7
