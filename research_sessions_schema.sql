-- Missing research_sessions table for Cheetah Research App
-- Execute this in your Supabase SQL editor to fix the missing table

-- 1. Create research_sessions table (for ongoing sessions)
CREATE TABLE IF NOT EXISTS research_sessions (
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

-- 2. Enable Row Level Security (RLS) on research_sessions
ALTER TABLE research_sessions ENABLE ROW LEVEL SECURITY;

-- 3. Create RLS policies for research_sessions
-- Users can only access their own research sessions
CREATE POLICY "Users can view own research sessions" ON research_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own research sessions" ON research_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own research sessions" ON research_sessions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own research sessions" ON research_sessions
    FOR DELETE USING (auth.uid() = user_id);

-- 4. Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_status ON research_sessions(status);
CREATE INDEX IF NOT EXISTS idx_research_sessions_session_id ON research_sessions(session_id);

-- 5. Add missing columns to research_history if they don't exist
ALTER TABLE research_history 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'completed';

-- 6. Create function to automatically move completed sessions to history
CREATE OR REPLACE FUNCTION move_completed_session_to_history()
RETURNS TRIGGER AS $$
BEGIN
    -- If session status changed to 'completed', insert into research_history
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        INSERT INTO research_history (
            user_id, query, final_result, agent_results, total_time, 
            agents, status, created_at, updated_at
        ) VALUES (
            NEW.user_id, NEW.query, NEW.final_result, 
            '[]'::jsonb, NEW.total_time, NEW.agents, 
            'completed', NEW.created_at, NOW()
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 7. Create trigger to automatically copy completed sessions to history
DROP TRIGGER IF EXISTS trigger_move_completed_session ON research_sessions;
CREATE TRIGGER trigger_move_completed_session
    AFTER UPDATE ON research_sessions
    FOR EACH ROW
    EXECUTE FUNCTION move_completed_session_to_history();