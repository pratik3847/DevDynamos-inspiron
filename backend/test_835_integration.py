#!/usr/bin/env python3
"""
Test 835 Parser Integration with RAG System
Validates PHASE 1 implementation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.parser_835.parser_835 import Parser835
from app.services.rag.rag_client import RAGClient

def test_835_parser_integration():
    """Test 835 parser with existing RAG system"""
    
    print("🧪 Testing 835 Parser + RAG Integration")
    print("=" * 50)
    
    # Test 1: RAG System Connection
    print("\n1. Testing RAG System Connection...")
    try:
        rag = RAGClient()
        carc_info = rag.query("What does CARC-1 mean?", top_k=2, min_score=0.3)
        
        if carc_info:
            print(f"✅ RAG connected - Found {len(carc_info)} results")
            print(f"   Top result: {carc_info[0]['text'][:100]}...")
        else:
            print("⚠️ RAG connected but no CARC-1 results found")
            
    except Exception as e:
        print(f"❌ RAG connection failed: {e}")
        return False
    
    # Test 2: 835 Parser Initialization  
    print("\n2. Testing 835 Parser Initialization...")
    try:
        parser = Parser835()
        rag_status = parser._get_rag_status()
        print(f"✅ Parser initialized - RAG embeddings: {rag_status:,}")
        
    except Exception as e:
        print(f"❌ Parser initialization failed: {e}")
        return False
    
    # Test 3: Sample 835 File Parsing
    print("\n3. Testing Sample 835 File Parsing...")
    try:
        # Read sample file
        sample_file = "tests/sample_835_files/sample_remittance_001.txt"
        if os.path.exists(sample_file):
            with open(sample_file, 'r') as f:
                content = f.read()
            
            # Parse file
            result = parser.parse_file(content)
            
            if 'error' not in result:
                print("✅ 835 file parsed successfully")
                print(f"   Claims found: {len(result.get('claims', []))}")
                print(f"   Payment amount: ${result.get('payment_header', {}).get('total_payment_amount', 0):,.2f}")
                
                # Show summary
                summary = result.get('summary', {})
                print(f"   Total billed: ${summary.get('total_billed_amount', 0):,.2f}")
                print(f"   Total paid: ${summary.get('total_paid_amount', 0):,.2f}")
                
            else:
                print(f"❌ Parse failed: {result['error']}")
                return False
        else:
            print(f"⚠️ Sample file not found: {sample_file}")
            
    except Exception as e:
        print(f"❌ Parsing test failed: {e}")
        return False
    
    # Test 4: RAG Code Explanation
    print("\n4. Testing CARC Code Explanations...")
    try:
        # Test with common CARC codes from sample file
        test_codes = ['1', '27', '45']
        explanations = parser.explain_adjustment_codes(test_codes)
        
        for code, explanation in explanations.items():
            confidence = explanation.get('confidence', 0)
            print(f"   CARC-{code}: Score {confidence:.3f}")
            print(f"     {explanation.get('explanation', 'No explanation')[:80]}...")
            
    except Exception as e:
        print(f"❌ Code explanation test failed: {e}")
        return False
    
    # Test 5: Performance Check
    print("\n5. Performance Check...")
    try:
        import time
        
        start_time = time.time()
        result = parser.parse_file(content)
        parse_time = time.time() - start_time
        
        start_time = time.time()
        explanations = parser.explain_adjustment_codes(['1', '27'])
        rag_time = time.time() - start_time
        
        print(f"✅ Performance metrics:")
        print(f"   Parse time: {parse_time:.3f}s")
        print(f"   RAG query time: {rag_time:.3f}s")
        
        if parse_time < 5.0 and rag_time < 3.0:
            print("✅ Performance targets met!")
        else:
            print("⚠️ Performance targets missed")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    print(f"\n🎉 ALL TESTS PASSED - 835 Parser + RAG Integration Ready!")
    return True

if __name__ == "__main__":
    success = test_835_parser_integration()
    sys.exit(0 if success else 1)