#!/usr/bin/env python3
"""
Test script for deep research functionality
"""

import asyncio
import websockets
import json
import time
import requests

async def test_deep_research():
    print("🧪 Testing Deep Research Functionality")
    print("=" * 50)
    
    # Test backend health
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print("❌ Backend health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Test WebSocket connection
    try:
        uri = "ws://localhost:8000/ws/test_client"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Send a test query
            test_query = "What are the latest trends in sustainable fashion for 2024?"
            print(f"🔍 Testing query: {test_query}")
            
            # Send the query
            message = {
                "type": "start_research",
                "data": {
                    "query": test_query,
                    "user_id": "test_user_123"
                }
            }
            
            await websocket.send(json.dumps(message))
            print("📤 Query sent")
            
            # Listen for responses
            start_time = time.time()
            timeout = 60  # 60 seconds timeout
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    print(f"📥 Received: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'session_created':
                        print(f"✅ Session created: {data.get('data', {}).get('session_id')}")
                    
                    elif data.get('type') == 'task_decomposed':
                        print("✅ Task decomposition completed")
                        subtasks = data.get('data', {}).get('subtasks', [])
                        print(f"📋 Subtasks: {len(subtasks)}")
                        for i, subtask in enumerate(subtasks):
                            print(f"   {i+1}. {subtask[:50]}...")
                    
                    elif data.get('type') == 'agent_progress':
                        agent_id = data.get('data', {}).get('agent_id')
                        status = data.get('data', {}).get('status')
                        progress = data.get('data', {}).get('progress', 0)
                        print(f"🤖 Agent {agent_id}: {status} ({progress}%)")
                    
                    elif data.get('type') == 'research_complete':
                        print("✅ Research completed!")
                        result = data.get('data', {}).get('final_result', '')
                        print(f"📄 Result length: {len(result)} characters")
                        break
                    
                    elif data.get('type') == 'error':
                        print(f"❌ Error: {data.get('data', {}).get('message', 'Unknown error')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for response...")
                    continue
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            if time.time() - start_time >= timeout:
                print("⏰ Test timed out after 60 seconds")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_deep_research()) 