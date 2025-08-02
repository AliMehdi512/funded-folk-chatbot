#!/usr/bin/env python3
"""
Test script to find correct OpenRouter free model IDs
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_openrouter_models():
    """Test different OpenRouter model IDs to find working ones"""
    
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return
    
    # Test different model IDs that might be available
    test_models = [
        "google/gemma-3n-e2b-it:free",
        "google/gemma-3n-e2b-it",
        "meta-llama/llama-3.1-8b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct",
        "meta-llama/llama-3.1-1b-instruct:free",
        "meta-llama/llama-3.1-1b-instruct",
        "microsoft/phi-3-mini-4k-instruct:free",
        "microsoft/phi-3-mini-4k-instruct",
        "mistralai/mistral-7b-instruct:free",
        "mistralai/mistral-7b-instruct",
        "anthropic/claude-3-haiku:free",
        "anthropic/claude-3-haiku",
        "openai/gpt-3.5-turbo:free",
        "openai/gpt-3.5-turbo"
    ]
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_prompt = "Hello, this is a test message."
    
    working_models = []
    
    for model in test_models:
        print(f"\n🔍 Testing model: {model}")
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": test_prompt}],
            "temperature": 0.1,
            "max_tokens": 50,
            "stream": False
        }
        
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ SUCCESS: {model}")
                working_models.append(model)
            elif response.status_code == 400:
                error_data = response.json()
                print(f"❌ 400 Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            elif response.status_code == 429:
                print(f"⚠️ 429 Rate limit for: {model}")
            else:
                print(f"❌ {response.status_code} Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print(f"\n🎉 Working models found: {len(working_models)}")
    for model in working_models:
        print(f"  ✅ {model}")

if __name__ == "__main__":
    test_openrouter_models() 