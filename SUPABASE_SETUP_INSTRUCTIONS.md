# 🔧 Fix Supabase Database Issues

Your Make It Heavy app has RLS (Row Level Security) policy violations. Here's how to fix them:

## 🚨 CRITICAL: Get Your Service Role Key

The backend needs your **SERVICE ROLE KEY** (not the anonymous key) to bypass RLS policies.

### Step 1: Get Service Role Key from Supabase
1. Go to your Supabase project: https://supabase.com/dashboard/project/xkooxszqjcvpsxrdroez
2. Click on **Settings** (⚙️) in the left sidebar
3. Click on **API** 
4. Copy the **`service_role`** key (NOT the `anon` key)
5. **IMPORTANT**: This key has admin privileges - keep it secret!

### Step 2: Update Backend Configuration
Replace the placeholder service key in `backend.py` line 58:

```python
# Replace this placeholder:
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhrb294c3pxamN2cHN4cmRyb2V6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE1MzU3MCwiZXhwIjoyMDY5NzI5NTcwfQ.Cj4YK7M7V-xn_5Y_Gy_wC8XS4Y4X7ZiYXd4QUUGqBE0"

# With your actual service role key:
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.YOUR_ACTUAL_SERVICE_ROLE_KEY_HERE"
```

## 🗄️ Fix Database Schema

### Step 1: Execute Database Fix Script
1. Go to your Supabase project
2. Click on **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy the entire content of `fix_supabase_database.sql`
5. Paste it and click **Run**

### Step 2: Verify Tables Were Created
You should see output like:
```
✅ research_sessions table created successfully
✅ research_history table created successfully
🎯 Database fix completed successfully!
```

## 🧪 Test the Fix

### Step 1: Restart Your Application
```bash
# Stop the current server (Ctrl+C)
# Then restart:
./launch.sh
```

### Step 2: Test Database Operations
1. Open http://localhost:5173
2. Start a research query
3. Check that you NO LONGER see these errors:
   - ❌ `"new row violates row-level security policy"`
   - ❌ `Failed to save session to Supabase`

### Step 3: Verify Data is Being Saved
1. Go to Supabase project → **Table Editor**
2. Check `research_sessions` table - should have your active sessions
3. Check `research_history` table - should have completed research

## 🔒 What Was Fixed

1. **RLS Policy Violation**: Backend now uses service role key that bypasses RLS
2. **Missing Tables**: Created proper `research_sessions` and `research_history` tables
3. **Status Error**: Fixed missing status attribute in research process
4. **User Isolation**: Each user can only see their own data
5. **Backend Operations**: Service role can perform all operations needed

## 🚀 Expected Behavior After Fix

- ✅ Sessions save to database without RLS errors
- ✅ Research history persists between sessions
- ✅ Users only see their own data
- ✅ Backend can perform all necessary operations
- ✅ No more `'status'` errors in research process

## 🆘 If You Still Have Issues

1. **Double-check the service role key** - make sure it's the right one
2. **Verify database script ran successfully** - check for any error messages
3. **Restart the backend** - make sure changes are loaded
4. **Check browser console** - look for any frontend errors

The app should now work properly with full database persistence!