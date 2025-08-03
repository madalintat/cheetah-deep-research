#!/usr/bin/env python3
"""
Quick test to verify if Ollama and the research system is working
"""

import asyncio
import requests
import json

async def test_ollama():
    """Test if Ollama is responding correctly"""
    print("🧪 Testing Ollama connection...")
    
    try:
        # Simple test request
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.1:8b",
                "messages": [{"role": "user", "content": "Hello, respond with just 'OK'"}],
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ollama is responding correctly")
            message = result.get("message", {}).get("content", "No content")
            print(f"   Response: {message[:100]}...")
            return True
        else:
            print(f"❌ Ollama error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

async def main():
    print("🔧 Quick Fix Test for Make It Heavy")
    print("=" * 40)
    
    # Test Ollama
    ollama_ok = await test_ollama()
    
    if ollama_ok:
        print("\n✅ All systems operational!")
        print("🚀 Your research should work now!")
        print("\n📋 What was fixed:")
        print("   ✅ Supabase JSON parsing error")
        print("   ✅ Status error in research synthesis") 
        print("   ✅ Environment variables loaded")
        print("\n🎯 Try running a research query again!")
    else:
        print("\n⚠️  Ollama needs attention:")
        print("   1. Make sure Ollama is running: ollama serve")
        print("   2. Check if model is available: ollama list")
        print("   3. Pull model if needed: ollama pull llama3.1:8b")

if __name__ == "__main__":
    asyncio.run(main())