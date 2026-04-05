#!/usr/bin/env python3
"""RAG performance and quality analysis."""

import time
from app.services.rag.rag_client import RAGClient

def test_rag_performance():
    """Test RAG retrieval performance and quality."""
    print("🧪 Testing RAG retrieval performance...")
    rag = RAGClient()
    
    test_queries = [
        "What is Loop 2000B in 837P?",
        "How do I validate NM1 segment?", 
        "What are the rules for CLM segment?",
        "Explain PER segment usage"
    ]
    
    total_time = 0
    total_results = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        
        start = time.time()
        results = rag.query(query, top_k=5)
        query_time = time.time() - start
        total_time += query_time
        total_results += len(results)
        
        print(f"⏱️ Query time: {query_time:.3f}s")
        print(f"📊 Results: {len(results)} chunks")
        
        if results:
            top_result = results[0]
            print(f"🎯 Top score: {top_result.get('score', 0):.3f}")
            print(f"📄 Sample: {top_result.get('text', '')[:80]}...")
            print(f"📚 Source: {top_result.get('source_doc', 'unknown')}")
            print(f"📖 Page: {top_result.get('page', 'N/A')}")
            print(f"🏷️ Doc type: {top_result.get('doc_type', 'unknown')}")
        else:
            print("❌ No results found")
    
    # Summary
    avg_time = total_time / len(test_queries)
    avg_results = total_results / len(test_queries)
    
    print(f"\n📈 PERFORMANCE SUMMARY:")
    print(f"⏱️ Average query time: {avg_time:.3f}s")
    print(f"📊 Average results per query: {avg_results:.1f}")
    print(f"🚀 Queries per second: {1/avg_time:.1f}")

if __name__ == "__main__":
    test_rag_performance()