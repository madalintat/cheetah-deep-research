-- ===============================================
-- CLEAN SLATE DATABASE RESET FOR CHEETAH RESEARCH APP
-- ===============================================
-- Execute this entire script in your Supabase SQL Editor
-- This will delete all existing research data and recreate tables

-- 1. DROP EXISTING TABLES COMPLETELY (including all data)
DROP TABLE IF EXISTS research_sessions CASCADE;
DROP TABLE IF EXISTS research_history CASCADE;

-- 2. CREATE RESEARCH_SESSIONS TABLE (for active/ongoing research)
CREATE TABLE research_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    session_id TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    status TEXT DEFAULT 'ongoing' CHECK (status IN ('ongoing', 'completed', 'failed')),
    current_phase TEXT DEFAULT 'initializing',
    agents JSONB DEFAULT '[]',
    progress FLOAT DEFAULT 0,
    final_result TEXT,
    total_time FLOAT DEFAULT 0,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. CREATE RESEARCH_HISTORY TABLE (for completed research)
CREATE TABLE research_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    query TEXT NOT NULL,
    final_result TEXT,
    agent_results JSONB DEFAULT '[]',
    total_time FLOAT DEFAULT 0,
    agents JSONB DEFAULT '[]',
    status TEXT DEFAULT 'completed',
    completed_count INTEGER DEFAULT 0,
    hunters_per_minute FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. ENABLE ROW LEVEL SECURITY (RLS)
ALTER TABLE research_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_history ENABLE ROW LEVEL SECURITY;

-- 5. CREATE RLS POLICIES FOR RESEARCH_SESSIONS
-- Users can only access their own research sessions
CREATE POLICY "Users can view own research sessions" ON research_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own research sessions" ON research_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own research sessions" ON research_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own research sessions" ON research_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- 6. CREATE RLS POLICIES FOR RESEARCH_HISTORY
-- Users can only access their own research history
CREATE POLICY "Users can view own research history" ON research_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own research history" ON research_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own research history" ON research_history
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own research history" ON research_history
    FOR DELETE USING (auth.uid() = user_id);

-- 7. CREATE PERFORMANCE INDEXES
CREATE INDEX idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX idx_research_sessions_status ON research_sessions(status);
CREATE INDEX idx_research_sessions_session_id ON research_sessions(session_id);
CREATE INDEX idx_research_sessions_created_at ON research_sessions(created_at);

CREATE INDEX idx_research_history_user_id ON research_history(user_id);
CREATE INDEX idx_research_history_created_at ON research_history(created_at);

-- 8. CREATE TRIGGER FUNCTION TO AUTO-UPDATE timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 9. CREATE TRIGGERS FOR AUTO-UPDATING TIMESTAMPS
CREATE TRIGGER update_research_sessions_updated_at
    BEFORE UPDATE ON research_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_history_updated_at
    BEFORE UPDATE ON research_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 10. OPTIONAL: CREATE FUNCTION TO AUTOMATICALLY ARCHIVE COMPLETED SESSIONS
-- This moves completed sessions to history (you can enable this if desired)
CREATE OR REPLACE FUNCTION archive_completed_session()
RETURNS TRIGGER AS $$
BEGIN
    -- If session status changed to 'completed', optionally copy to history
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- This trigger is disabled by default to avoid duplicates
        -- Enable only if you want automatic archiving
        NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 11. VERIFY TABLES WERE CREATED CORRECTLY
DO $$
BEGIN
    -- Check if tables exist and display confirmation
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'research_sessions') THEN
        RAISE NOTICE '✅ research_sessions table created successfully';
    END IF;
    
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'research_history') THEN
        RAISE NOTICE '✅ research_history table created successfully';
    END IF;
    
    RAISE NOTICE '🎯 Clean slate database setup completed!';
    RAISE NOTICE '📊 You can now:';
    RAISE NOTICE '   - Start new research sessions';
    RAISE NOTICE '   - Track active progress in research_sessions';
    RAISE NOTICE '   - Store completed research in research_history';
    RAISE NOTICE '   - Refresh page while research is running';
    RAISE NOTICE '   - View history in the left sidebar';
END $$;