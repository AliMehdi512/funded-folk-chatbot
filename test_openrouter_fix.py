#!/usr/bin/env python3
"""
Test script for OpenRouter rate limiting fixes
"""

import os
import time
from dotenv import load_dotenv
from hybrid_rag_system import HybridRAGSystem

load_dotenv()

def test_openrouter_fixes():
    """Test the OpenRouter rate limiting improvements"""
    
    # Check if API key is available
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("Please set your OpenRouter API key in .env file")
        return
    
    print("🚀 Testing OpenRouter rate limiting fixes...")
    
    # Initialize RAG system
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
        "What are the pricing options?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        start_time = time.time()
        
        try:
            response = rag.chat(query)
            end_time = time.time()
            
            print(f"✅ Response received in {end_time - start_time:.2f}s")
            print(f"Response: {response[:200]}...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Brief pause between tests
        if i < len(test_queries):
            print("⏳ Waiting 2 seconds before next test...")
            time.sleep(2)
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    test_openrouter_fixes() 