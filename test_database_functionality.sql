-- ===============================================
-- TEST DATABASE FUNCTIONALITY
-- ===============================================
-- Run this AFTER executing clean_slate_database.sql
-- This verifies that everything is working correctly

-- 1. VERIFY TABLES EXIST
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_name IN ('research_sessions', 'research_history')
ORDER BY table_name;

-- 2. VERIFY COLUMNS ARE CORRECT
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('research_sessions', 'research_history')
ORDER BY table_name, ordinal_position;

-- 3. VERIFY RLS POLICIES EXIST
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE tablename IN ('research_sessions', 'research_history')
ORDER BY tablename, policyname;

-- 4. VERIFY INDEXES EXIST
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('research_sessions', 'research_history')
ORDER BY tablename, indexname;

-- 5. TEST INSERT PERMISSIONS (Replace with your user ID)
-- Get current user ID first
SELECT auth.uid() as current_user_id;

-- Test inserting a research session (this should work)
-- NOTE: Replace 'your-user-id-here' with actual user ID from above query
/*
INSERT INTO research_sessions (
    user_id, 
    session_id, 
    query, 
    status, 
    current_phase
) VALUES (
    'your-user-id-here',  -- Replace with your actual user ID
    'test-session-001',
    'Test research query',
    'ongoing',
    'testing'
);
*/

-- Test inserting research history (this should work)
/*
INSERT INTO research_history (
    user_id,
    query,
    final_result,
    agent_results,
    total_time,
    status
) VALUES (
    'your-user-id-here',  -- Replace with your actual user ID
    'Test completed research',
    'This is a test result',
    '[]'::jsonb,
    120.5,
    'completed'
);
*/

-- 6. VERIFY DATA CAN BE RETRIEVED
/*
SELECT 
    session_id,
    query,
    status,
    current_phase,
    progress,
    created_at
FROM research_sessions 
WHERE user_id = 'your-user-id-here'  -- Replace with your actual user ID
ORDER BY created_at DESC;

SELECT 
    id,
    query,
    status,
    total_time,
    created_at
FROM research_history 
WHERE user_id = 'your-user-id-here'  -- Replace with your actual user ID
ORDER BY created_at DESC;
*/

-- 7. CLEANUP TEST DATA (uncomment to remove test records)
/*
DELETE FROM research_sessions WHERE session_id = 'test-session-001';
DELETE FROM research_history WHERE query = 'Test completed research';
*/

-- 8. FINAL VERIFICATION MESSAGE
DO $$
BEGIN
    RAISE NOTICE '✅ Database verification completed!';
    RAISE NOTICE '📝 To test functionality:';
    RAISE NOTICE '   1. Get your user ID: SELECT auth.uid()';
    RAISE NOTICE '   2. Uncomment test queries above and replace user ID';
    RAISE NOTICE '   3. Run the insert/select queries';
    RAISE NOTICE '   4. Start a research session in your app';
    RAISE NOTICE '   5. Refresh the page and verify persistence';
END $$;