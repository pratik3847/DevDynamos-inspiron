"""Test script for RAG service integration."""
from app.services.rag import RAGClient

def test_rag_connection():
    """Test RAG client initialization and connection."""
    print("\n🧪 Testing RAG Service Connection...")
    print("=" * 50)
    
    try:
        rag = RAGClient()
        stats = rag.get_stats()
        
        print(f"✅ RAG Client connected successfully!")
        print(f"📊 Collection: {stats.get('name', 'N/A')}")
        print(f"📈 Total embeddings: {stats.get('vectors_count', 0):,}")
        print(f"✨ Status: {stats.get('status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_basic_query():
    """Test basic query functionality."""
    print("\n🔍 Testing Basic Query...")
    print("=" * 50)
    
    try:
        rag = RAGClient()
        results = rag.query("What is Loop 2310B in 837P?", top_k=3)
        
        if results:
            print(f"✅ Found {len(results)} results")
            print(f"\n📄 Top result:")
            print(f"   Source: {results[0]['source_doc']}")
            print(f"   Page: {results[0]['page']}")
            print(f"   Score: {results[0]['score']:.2%}")
            print(f"   Text: {results[0]['text'][:200]}...")
            return True
        else:
            print("⚠️  No results found")
            return False
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

def test_transaction_filter():
    """Test transaction type filtering."""
    print("\n🎯 Testing Transaction Filter...")
    print("=" * 50)
    
    try:
        rag = RAGClient()
        results = rag.search_by_transaction(
            "Required segments",
            transaction_type="837P",
            top_k=3
        )
        
        if results:
            print(f"✅ Found {len(results)} 837P-specific results")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['source_doc']} (score: {result['score']:.2%})")
            return True
        else:
            print("⚠️  No results found")
            return False
    except Exception as e:
        print(f"❌ Transaction filter failed: {e}")
        return False

def test_code_lookup():
    """Test code list lookup."""
    print("\n💉 Testing Code Lookup...")
    print("=" * 50)
    
    try:
        rag = RAGClient()
        results = rag.search_code_lists("A00", top_k=2)
        
        if results:
            print(f"✅ Found {len(results)} ICD-10 code results")
            for result in results:
                print(f"   Code: {result['text'][:100]}")
            return True
        else:
            print("⚠️  No code results found")
            return False
    except Exception as e:
        print(f"❌ Code lookup failed: {e}")
        return False

def test_agent_integration_example():
    """Example showing how agents should use RAG."""
    print("\n🤖 Agent Integration Example...")
    print("=" * 50)
    
    try:
        rag = RAGClient()
        
        # Simulate validator agent querying RAG
        print("\n1️⃣ Validator Agent Query:")
        validation_context = rag.query(
            "What segments are required in Loop 2310B for 837P?",
            transaction_type="837P",
            top_k=2
        )
        print(f"   Found {len(validation_context)} validation rules")
        
        # Simulate fix agent querying RAG
        print("\n2️⃣ Fix Agent Query:")
        fix_context = rag.query(
            "How to add NM1 segment in 837P?",
            transaction_type="837P",
            top_k=2
        )
        print(f"   Found {len(fix_context)} fix instructions")
        
        # Simulate explainer agent querying RAG
        print("\n3️⃣ Explainer Agent Query:")
        explanation_context = rag.query(
            "Why is rendering provider required in 837P?",
            transaction_type="837P",
            doc_type="tr3",
            top_k=2
        )
        print(f"   Found {len(explanation_context)} explanations")
        
        print("\n✅ All agents can successfully query RAG!")
        return True
    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🚀 RAG SERVICE INTEGRATION TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Connection Test", test_rag_connection),
        ("Basic Query Test", test_basic_query),
        ("Transaction Filter Test", test_transaction_filter),
        ("Code Lookup Test", test_code_lookup),
        ("Agent Integration Test", test_agent_integration_example)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG service is ready for integration.")
    else:
        print("⚠️  Some tests failed. Check configuration and try again.")
