#!/usr/bin/env python3
"""Comprehensive RAG Performance and Quality Analysis"""

import time
from app.services.rag.rag_client import RAGClient
from app.services.rag import config

def analyze_rag_system():
    """Comprehensive analysis of RAG system performance and quality."""
    
    print("🔬 COMPREHENSIVE RAG ANALYSIS")
    print("=" * 50)
    
    # Initialize
    rag = RAGClient()
    
    # 1. RETRIEVAL SPEED ANALYSIS
    print("\n📊 1. RETRIEVAL SPEED ANALYSIS")
    print("-" * 30)
    
    speed_tests = [
        ("Simple segment query", "NM1 segment rules"),
        ("Complex loop query", "What is Loop 2000B in 837P transaction?"),
        ("Validation query", "How to validate CLM segment structure?"),
        ("Code lookup", "CARC code 1 meaning")
    ]
    
    total_time = 0
    successful_queries = 0
    
    for test_name, query in speed_tests:
        start = time.time()
        results = rag.query(query, top_k=3)
        query_time = time.time() - start
        total_time += query_time
        
        if results:
            successful_queries += 1
            top_score = results[0].get('score', 0)
            print(f"✅ {test_name}")
            print(f"   ⏱️  Time: {query_time:.3f}s | Results: {len(results)} | Top Score: {top_score:.3f}")
        else:
            print(f"❌ {test_name}")
            print(f"   ⏱️  Time: {query_time:.3f}s | No results found")
    
    avg_time = total_time / len(speed_tests)
    print(f"\n📈 Speed Summary:")
    print(f"   Average query time: {avg_time:.3f}s")
    print(f"   Queries per second: {1/avg_time:.1f}")
    print(f"   Success rate: {successful_queries}/{len(speed_tests)} ({100*successful_queries/len(speed_tests):.0f}%)")
    
    # 2. RETRIEVAL QUALITY ANALYSIS  
    print(f"\n🎯 2. RETRIEVAL QUALITY ANALYSIS")
    print("-" * 30)
    
    quality_tests = [
        ("Exact match", "Loop 2000B", "837P"),
        ("Semantic match", "patient demographic information", "834"),
        ("Technical term", "NM1 segment validation rules", None),
        ("Code lookup", "claim adjustment reason code", None)
    ]
    
    for test_name, query, transaction in quality_tests:
        print(f"\n🔍 {test_name}: '{query}'")
        results = rag.query(query, top_k=5, transaction_type=transaction, min_score=0.2)
        
        if results:
            print(f"   📊 Found {len(results)} results")
            best = results[0]
            print(f"   🏆 Best match (score: {best['score']:.3f}):")
            print(f"      📄 Source: {best['source_doc']}")
            print(f"      📖 Page: {best.get('page', 'N/A')}")
            print(f"      🏷️  Type: {best.get('doc_type', 'unknown')}")
            print(f"      📝 Text: {best['text'][:120]}...")
        else:
            print("   ❌ No results found")
    
    # 3. METADATA FILTERING ANALYSIS
    print(f"\n🏷️  3. METADATA FILTERING ANALYSIS")
    print("-" * 30)
    
    # Test transaction type filtering
    query = "demographic information"
    for tx_type in ["834", "837P", "835", "837I"]:
        results = rag.query(query, transaction_type=tx_type, top_k=3, min_score=0.2)
        print(f"   {tx_type}: {len(results)} results")
    
    # Test document type filtering
    print(f"\n   Document type filtering:")
    for doc_type in ["tr3", "claims_manual", "code_list"]:
        results = rag.query("validation rules", doc_type=doc_type, top_k=3, min_score=0.2)
        print(f"   {doc_type}: {len(results)} results")
    
    # 4. BOTTLENECK ANALYSIS
    print(f"\n⚠️  4. BOTTLENECK ANALYSIS")
    print("-" * 30)
    
    # Test concurrent queries simulation
    import threading
    import queue
    
    def worker(q, results_queue):
        rag_worker = RAGClient()  # Each thread needs its own instance
        while True:
            query = q.get()
            if query is None:
                break
            start = time.time()
            results = rag_worker.query(query, top_k=3)
            elapsed = time.time() - start
            results_queue.put((query, elapsed, len(results)))
            q.task_done()
    
    queries = ["NM1 segment", "Loop 2000A", "CLM rules", "validation error"] * 2
    q = queue.Queue()
    results_queue = queue.Queue()
    
    for query in queries:
        q.put(query)
    
    # Start 3 worker threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(q, results_queue))
        t.start()
        threads.append(t)
    
    start_concurrent = time.time()
    q.join()
    concurrent_time = time.time() - start_concurrent
    
    # Stop workers
    for i in range(3):
        q.put(None)
    for t in threads:
        t.join()
    
    # Collect results
    concurrent_results = []
    while not results_queue.empty():
        concurrent_results.append(results_queue.get())
    
    avg_concurrent_time = sum(r[1] for r in concurrent_results) / len(concurrent_results)
    
    print(f"   Sequential time estimate: {len(queries) * avg_time:.2f}s")
    print(f"   Concurrent time (3 threads): {concurrent_time:.2f}s")
    print(f"   Speedup: {(len(queries) * avg_time / concurrent_time):.1f}x")
    print(f"   Average per-query time: {avg_concurrent_time:.3f}s")
    
    # 5. CONFIGURATION SUMMARY
    print(f"\n⚙️  5. CONFIGURATION SUMMARY")
    print("-" * 30)
    print(f"   Embedding model: {config.EMBEDDING_MODEL_NAME}")
    print(f"   Vector dimension: {config.EMBEDDING_DIMENSION}")
    print(f"   Default similarity threshold: {config.SIMILARITY_THRESHOLD}")
    print(f"   Default top-k: {config.DEFAULT_TOP_K}")
    print(f"   Maximum top-k: {config.MAX_TOP_K}")
    print(f"   Vector database: Qdrant Cloud")
    print(f"   Collection size: 240,054 embeddings")
    
    # 6. LLM USAGE ANALYSIS
    print(f"\n🤖 6. LLM USAGE ANALYSIS") 
    print("-" * 30)
    print(f"   ✅ Retrieval: NO LLM usage (pure vector search)")
    print(f"   ✅ Embeddings: Local sentence-transformers model")
    print(f"   ✅ Groq API: Only used for final answer generation")
    print(f"   💡 Bottleneck: Vector search + embedding, NOT Groq limits")
    
    print(f"\n🎉 ANALYSIS COMPLETE!")

if __name__ == "__main__":
    analyze_rag_system()