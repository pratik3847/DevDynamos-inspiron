from app.services.rag.rag_client import RAGClient

# Test with lower similarity threshold
rag = RAGClient()
results = rag.query('Loop 2000B', top_k=5, min_score=0.3)
print(f'Results with min_score=0.3: {len(results)}')

# Test with even lower threshold  
results = rag.query('Loop 2000B', top_k=5, min_score=0.1)
print(f'Results with min_score=0.1: {len(results)}')

# Test with no threshold
results = rag.query('Loop 2000B', top_k=5, min_score=0.0)
print(f'Results with min_score=0.0: {len(results)}')

if results:
    print(f'Top score: {results[0].get("score", 0):.3f}')
    print(f'Text sample: {results[0].get("text", "")[:80]}...')