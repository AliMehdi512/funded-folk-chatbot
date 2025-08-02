#!/usr/bin/env python3
"""
Stress test script to make 100 requests to test OpenRouter rate limiting
"""

import os
import time
import requests
import json
from dotenv import load_dotenv
from hybrid_rag_system import HybridRAGSystem

load_dotenv()

def stress_test_100_requests():
    """Make 100 requests to test rate limiting and model rotation"""
    
    # Check if API key is available
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not found in environment")
        return
    
    print("🚀 Starting stress test with 100 requests...")
    
    # Initialize RAG system
    try:
        rag = HybridRAGSystem()
        print("✅ RAG system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        return
    
    # Test queries (cycling through different types)
    test_queries = [
        "What is Funded Folk?",
        "How do I get started?",
        "What are the pricing options?",
        "How does the challenge work?",
        "What are the trading rules?",
        "How do I withdraw profits?",
        "What platforms do you support?",
        "How long does account delivery take?",
        "What is the maximum drawdown?",
        "How do I contact support?"
    ]
    
    # Statistics tracking
    stats = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'fallback_responses': 0,
        'models_used': {},
        'response_times': [],
        'errors': []
    }
    
    start_time = time.time()
    
    for i in range(100):
        query = test_queries[i % len(test_queries)]
        request_start = time.time()
        
        print(f"\n--- Request {i+1}/100: {query[:50]}... ---")
        
        try:
            response = rag.chat(query)
            request_time = time.time() - request_start
            
            # Track statistics
            stats['total_requests'] += 1
            stats['response_times'].append(request_time)
            
            # Check if it's a fallback response
            if "Based on the available information:" in response or "I'm currently experiencing technical difficulties" in response:
                stats['fallback_responses'] += 1
                print(f"📝 Fallback response (time: {request_time:.2f}s)")
            else:
                stats['successful_requests'] += 1
                print(f"✅ Success (time: {request_time:.2f}s)")
            
            # Track model usage (this would need to be enhanced in the RAG system)
            # For now, we'll just track success/failure
            
        except Exception as e:
            request_time = time.time() - request_start
            stats['failed_requests'] += 1
            stats['errors'].append(str(e))
            print(f"❌ Error: {str(e)[:100]}... (time: {request_time:.2f}s)")
        
        # Brief pause between requests to avoid overwhelming
        if i < 99:  # Don't pause after the last request
            time.sleep(0.5)
    
    total_time = time.time() - start_time
    
    # Print final statistics
    print(f"\n🎉 Stress test completed!")
    print(f"📊 Statistics:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Successful: {stats['successful_requests']}")
    print(f"   Failed: {stats['failed_requests']}")
    print(f"   Fallback responses: {stats['fallback_responses']}")
    print(f"   Success rate: {(stats['successful_requests']/stats['total_requests']*100):.1f}%")
    print(f"   Average response time: {sum(stats['response_times'])/len(stats['response_times']):.2f}s")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Requests per minute: {(stats['total_requests']/total_time*60):.1f}")
    
    if stats['errors']:
        print(f"\n❌ Errors encountered:")
        for error in stats['errors'][:5]:  # Show first 5 errors
            print(f"   - {error[:100]}...")
        if len(stats['errors']) > 5:
            print(f"   ... and {len(stats['errors'])-5} more errors")

if __name__ == "__main__":
    stress_test_100_requests() 