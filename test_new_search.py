#!/usr/bin/env python3
"""
Test script for the new revolutionary Crawl4AI + OLLAMA search tool
"""

import asyncio
import sys
import os
import yaml

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.search_tool import SearchTool

async def test_new_search():
    """Test the new Crawl4AI + OLLAMA search functionality"""
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create search tool instance
    search_tool = SearchTool(config)
    
    print("🚀 Testing Revolutionary Crawl4AI + OLLAMA Search Tool")
    print("=" * 60)
    
    # Test query
    test_query = "best hotels in Brasov Romania budget travel 2024"
    
    print(f"📝 Query: {test_query}")
    print(f"🤖 Using OLLAMA model: llama3.2:latest")
    print(f"🕷️ Primary: Crawl4AI + OLLAMA extraction")
    print(f"💰 Fallback: Tavily premium search")
    print("-" * 60)
    
    try:
        # Execute the new search
        results = await search_tool.execute(
            query=test_query,
            max_results=3,
            deep_extract=True
        )
        
        print(f"✅ Search completed! Found {len(results)} results")
        print("=" * 60)
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"\n🔍 RESULT {i}:")
            print(f"   URL: {result.get('url', 'N/A')}")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Content: {result.get('content', 'N/A')[:200]}...")
            print(f"   Key Facts: {len(result.get('key_facts', []))} facts")
            print(f"   Authority: {result.get('authority', 'N/A')}")
            print(f"   Extraction Success: {result.get('extraction_success', False)}")
            print(f"   Word Count: {result.get('word_count', 0)}")
            
            if result.get('source') == 'tavily_premium':
                print(f"   🔄 Source: Tavily Fallback (Crawl4AI insufficient)")
            else:
                print(f"   🤖 Source: Crawl4AI + OLLAMA")
        
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await search_tool.cleanup()

if __name__ == "__main__":
    asyncio.run(test_new_search())