#!/usr/bin/env python3
"""
Test script to demonstrate improved rate limiting strategy
"""

import os
import time
from dotenv import load_dotenv
from hybrid_rag_system import HybridRAGSystem

load_dotenv()

def test_improved_rate_limiting():
    """Test the improved rate limiting strategy"""
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not found in environment")
        return
    
    print("🚀 Testing improved rate limiting strategy...")
    
    try:
        rag = HybridRAGSystem()
        print("✅ RAG system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        return
    
    # Test queries
    test_queries = [
        "What is Funded Folk?",
        "How do I get started?",
        "What are the pricing options?",
        "How does the challenge work?",
        "What are the trading rules?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        start_time = time.time()
        
        try:
            response = rag.chat(query)
            end_time = time.time()
            
            print(f"✅ Response received in {end_time - start_time:.2f}s")
            print(f"Response preview: {response[:100]}...")
            
            # Show rate limiting status
            print(f"📊 Rate limiting status:")
            for model in ["mistralai/mistral-7b-instruct:free", "google/gemma-3n-e2b-it:free"]:
                is_available = rag._is_model_available(model, cooldown_seconds=120)
                is_rate_limited = rag._is_model_rate_limited(model, cooldown_seconds=300)
                status = "✅ Available" if is_available and not is_rate_limited else "⏳ Cooldown/Rate Limited"
                print(f"   {model}: {status}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Brief pause between tests
        if i < len(test_queries):
            print("⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    test_improved_rate_limiting() 