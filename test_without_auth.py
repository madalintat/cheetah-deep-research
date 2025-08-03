#!/usr/bin/env python3
"""
Test script that works without requiring authenticated users.
This tests the database connection and basic operations.
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
    
    async def test_direct_table_access(self):
        """Test direct table access using service role (bypasses RLS)"""
        print("🧪 Testing direct table access with service role...")
        
        try:
            # Test reading from research_sessions table
            response = requests.get(
                f"{self.url}/rest/v1/research_sessions?select=*&limit=1",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ Can access research_sessions table")
                sessions = response.json()
                print(f"   Found {len(sessions)} existing sessions")
            else:
                print(f"❌ Cannot access research_sessions: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
            
            # Test reading from research_history table
            response = requests.get(
                f"{self.url}/rest/v1/research_history?select=*&limit=1",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ Can access research_history table")
                history = response.json()
                print(f"   Found {len(history)} existing history records")
            else:
                print(f"❌ Cannot access research_history: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Table access test error: {e}")
            return False
    
    async def test_table_structure(self):
        """Test if tables have the correct structure"""
        print("🧪 Testing table structure...")
        
        try:
            # Get table info for research_sessions
            response = requests.get(
                f"{self.url}/rest/v1/research_sessions?select=*&limit=0",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ research_sessions table exists and is accessible")
            else:
                print("❌ research_sessions table missing or inaccessible")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
            
            # Get table info for research_history
            response = requests.get(
                f"{self.url}/rest/v1/research_history?select=*&limit=0",
                headers=self.headers
            )
            
            if response.status_code == 200:
                print("✅ research_history table exists and is accessible")
            else:
                print("❌ research_history table missing or inaccessible")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Table structure test error: {e}")
            return False
    
    async def test_auth_users_table(self):
        """Check if auth.users table exists and has users"""
        print("🧪 Testing auth.users table...")
        
        try:
            # Try to access auth.users table (might require special permissions)
            response = requests.get(
                f"{self.url}/rest/v1/auth.users?select=id&limit=5",
                headers=self.headers
            )
            
            if response.status_code == 200:
                users = response.json()
                print(f"✅ Found {len(users)} users in auth.users table")
                for user in users:
                    print(f"   User ID: {user.get('id', 'unknown')}")
                return True
            else:
                print(f"⚠️  Cannot access auth.users table: {response.status_code}")
                print(f"   This is normal - auth.users might not be directly accessible")
                print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️  Auth users test error: {e}")
            return False

async def run_tests():
    """Run all database tests without requiring auth"""
    print("🚀 Starting Database Structure Tests")
    print("=" * 50)
    
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("❌ ERROR: Missing required environment variables!")
        print("   Please create a .env file with SUPABASE_URL and SUPABASE_SERVICE_KEY")
        return
    
    print(f"🔌 Testing connection to: {SUPABASE_URL}")
    print(f"🔑 Using service role key: {SUPABASE_SERVICE_KEY[:50]}...")
    
    client = TestSupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # Test 1: Table structure
    structure_result = await client.test_table_structure()
    
    # Test 2: Direct table access
    access_result = await client.test_direct_table_access()
    
    # Test 3: Auth users (optional)
    auth_result = await client.test_auth_users_table()
    
    print("\n" + "=" * 50)
    print("🎯 DATABASE TESTS SUMMARY:")
    
    if structure_result:
        print("✅ Table structure: PASSED")
    else:
        print("❌ Table structure: FAILED")
    
    if access_result:
        print("✅ Table access: PASSED")
    else:
        print("❌ Table access: FAILED")
    
    if auth_result:
        print("✅ Auth system: ACCESSIBLE")
    else:
        print("⚠️  Auth system: LIMITED ACCESS (normal)")
    
    overall_success = structure_result and access_result
    
    if overall_success:
        print("\n🎉 DATABASE IS READY!")
        print("   ✅ Tables exist and are accessible")
        print("   ✅ Service role key works correctly")
        print("   ✅ Your app should work properly")
        print("\n📋 NEXT STEPS:")
        print("   1. Run your app: ./launch.sh")
        print("   2. Test with a real research query")
        print("   3. Check that sessions are saved to database")
    else:
        print("\n⚠️  DATABASE NEEDS SETUP:")
        print("   📄 Run the database schema in Supabase SQL Editor:")
        print("   1. Go to: https://supabase.com/dashboard/project/xkooxszqjcvpsxrdroez")
        print("   2. Click 'SQL Editor' → 'New Query'")
        print("   3. Copy content from: fix_supabase_database.sql")
        print("   4. Click 'Run' and wait for completion")
        print("   5. Re-run this test: python test_without_auth.py")

if __name__ == "__main__":
    asyncio.run(run_tests())