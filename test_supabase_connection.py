#!/usr/bin/env python3
"""
Test script to verify Supabase database operations work correctly.
Run this after applying the fixes to ensure everything is working.
"""

import asyncio
import json
import uuid
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

class TestSupabaseClient:
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    
    async def test_create_session(self):
        """Test creating a research session"""
        print("🧪 Testing research session creation...")
        
        # Generate test data - create a proper UUID format
        # Note: This test will fail with foreign key constraint because we're not creating a real user
        # But it will verify the database connection and table structure works
        test_user_id = "5cbf4038-1234-5678-9abc-def012345678"  # Proper UUID format for testing
        session_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()
        
        session_data = {
            "user_id": test_user_id,
            "session_id": session_id,
            "query": "Test query for database verification",
            "status": "ongoing",
            "current_phase": "testing",
            "agents": [],
            "progress": 0.5,
            "start_time": current_time,
            "last_updated": current_time
        }
        
        try:
            response = requests.post(
                f"{self.url}/rest/v1/research_sessions",
                headers=self.headers,
                json=session_data
            )
            
            if response.status_code in [200, 201]:
                print("✅ Session creation successful!")
                print(f"   Session ID: {session_id[:8]}...")
                return {"success": True, "session_id": session_id}
            else:
                print(f"❌ Session creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ Session creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_create_history(self):
        """Test creating research history"""
        print("🧪 Testing research history creation...")
        
        test_user_id = "5cbf4038-1234-5678-9abc-def012345678"  # Proper UUID format for testing
        
        history_data = {
            "user_id": test_user_id,
            "query": "Test historical research query",
            "final_result": "This is a test result to verify database operations work correctly.",
            "agent_results": [
                {"agent_id": 1, "result": "Test agent 1 result"},
                {"agent_id": 2, "result": "Test agent 2 result"}
            ],
            "total_time": 45.2,
            "agents": ["source_scout", "deep_analyst"],
            "status": "completed",
            "completed_count": 2,
            "hunters_per_minute": 2.67
        }
        
        try:
            response = requests.post(
                f"{self.url}/rest/v1/research_history",
                headers=self.headers,
                json=history_data
            )
            
            if response.status_code in [200, 201]:
                print("✅ History creation successful!")
                return {"success": True}
            else:
                print(f"❌ History creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ History creation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_read_operations(self):
        """Test reading data from tables"""
        print("🧪 Testing data retrieval...")
        
        try:
            # Test reading sessions
            response = requests.get(
                f"{self.url}/rest/v1/research_sessions?select=*&limit=5",
                headers=self.headers
            )
            
            if response.status_code == 200:
                sessions = response.json()
                print(f"✅ Retrieved {len(sessions)} sessions from database")
            else:
                print(f"❌ Failed to read sessions: {response.text}")
                return {"success": False}
            
            # Test reading history
            response = requests.get(
                f"{self.url}/rest/v1/research_history?select=*&limit=5",
                headers=self.headers
            )
            
            if response.status_code == 200:
                history = response.json()
                print(f"✅ Retrieved {len(history)} history records from database")
                return {"success": True}
            else:
                print(f"❌ Failed to read history: {response.text}")
                return {"success": False}
                
        except Exception as e:
            print(f"❌ Read operations error: {e}")
            return {"success": False, "error": str(e)}

async def run_tests():
    """Run all database tests"""
    print("🚀 Starting Supabase Database Tests")
    print("=" * 50)
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ ERROR: Missing required environment variables!")
        print("   Please create a .env file with SUPABASE_URL and SUPABASE_SERVICE_KEY")
        print("   Run: python create_env_file.py")
        return
    
    client = TestSupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Test 1: Create session
    session_result = await client.test_create_session()
    
    # Test 2: Create history
    history_result = await client.test_create_history()
    
    # Test 3: Read operations
    read_result = await client.test_read_operations()
    
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS SUMMARY:")
    
    if session_result.get("success"):
        print("✅ Session creation: PASSED")
    else:
        print("❌ Session creation: FAILED")
    
    if history_result.get("success"):
        print("✅ History creation: PASSED")
    else:
        print("❌ History creation: FAILED")
    
    if read_result.get("success"):
        print("✅ Data retrieval: PASSED")
    else:
        print("❌ Data retrieval: FAILED")
    
    all_passed = (session_result.get("success") and 
                  history_result.get("success") and 
                  read_result.get("success"))
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Your database is working correctly.")
        print("   You can now use the app and data will be properly saved.")
    else:
        print("\n⚠️ Some tests failed. Please check:")
        print("   1. Service role key is correct")
        print("   2. Database schema was executed successfully")
        print("   3. RLS policies are configured properly")

if __name__ == "__main__":
    asyncio.run(run_tests())