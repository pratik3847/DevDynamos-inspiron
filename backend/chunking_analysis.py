from app.services.rag.rag_client import RAGClient

# Check chunking strategy
rag = RAGClient()
results = rag.query('segment validation', min_score=0.2, top_k=15)

print('📝 CHUNKING STRATEGY ANALYSIS')
print('=' * 40)

if results:
    # Analyze chunk sizes and types
    chunk_sizes = []
    doc_types = set()
    sources = set()
    
    print(f"Sample of {len(results)} chunks:")
    for i, r in enumerate(results[:5], 1):
        text = r.get('text', '')
        chunk_sizes.append(len(text))
        doc_types.add(r.get('doc_type', 'unknown'))
        sources.add(r.get('source_doc', 'unknown'))
        
        print(f"\n{i}. {r.get('source_doc', 'unknown')[:30]}... (page {r.get('page', 'N/A')})")
        print(f"   Length: {len(text)} chars | Score: {r.get('score', 0):.3f}")
        print(f"   Type: {r.get('doc_type', 'unknown')}")
        print(f"   Text: {text[:80]}...")
    
    avg_size = sum(chunk_sizes) / len(chunk_sizes)
    print(f"\n📊 STATISTICS:")
    print(f"   Average chunk size: {avg_size:.0f} characters")
    print(f"   Size range: {min(chunk_sizes)} - {max(chunk_sizes)} characters")
    print(f"   Document types: {', '.join(doc_types)}")
    print(f"   Unique sources: {len(sources)}")
    
else:
    print("No results found for analysis")