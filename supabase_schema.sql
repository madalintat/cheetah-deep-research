-- Supabase Database Schema for Cheetah Research App
-- Execute this in your Supabase SQL editor

-- Enable RLS (Row Level Security)
-- This ensures users can only access their own data

-- 1. Create research_history table
CREATE TABLE IF NOT EXISTS research_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    query TEXT NOT NULL,
    final_result TEXT,
    agent_results JSONB,
    total_time FLOAT,
    agents JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create user_profiles table for additional user data
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    total_searches INTEGER DEFAULT 0,
    total_search_time FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Enable Row Level Security (RLS) on tables
ALTER TABLE research_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS policies for research_history
-- Users can only access their own research history
CREATE POLICY "Users can view own research history" ON research_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own research history" ON research_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own research history" ON research_history
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own research history" ON research_history
    FOR DELETE USING (auth.uid() = user_id);

-- 5. Create RLS policies for user_profiles
-- Users can only access their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- 6. Create function to automatically create user profile when user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name)
    VALUES (new.id, new.email, new.raw_user_meta_data->>'full_name');
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Create trigger to execute the function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- 8. Create function to update search statistics
CREATE OR REPLACE FUNCTION public.update_user_search_stats(
    p_user_id UUID,
    p_search_time FLOAT
)
RETURNS VOID AS $$
BEGIN
    UPDATE user_profiles 
    SET 
        total_searches = total_searches + 1,
        total_search_time = total_search_time + p_search_time,
        updated_at = NOW()
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 9. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_research_history_user_id ON research_history(user_id);
CREATE INDEX IF NOT EXISTS idx_research_history_created_at ON research_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- 10. Create view for research summary (optional)
CREATE OR REPLACE VIEW research_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.full_name,
    u.total_searches,
    u.total_search_time,
    COUNT(r.id) as stored_searches,
    AVG(r.total_time) as avg_search_time,
    MAX(r.created_at) as last_search_date
FROM user_profiles u
LEFT JOIN research_history r ON u.id = r.user_id
GROUP BY u.id, u.email, u.full_name, u.total_searches, u.total_search_time;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON public.research_history TO authenticated;
GRANT ALL ON public.user_profiles TO authenticated;
GRANT SELECT ON public.research_summary TO authenticated;
GRANT EXECUTE ON FUNCTION public.update_user_search_stats TO authenticated;

-- Example queries for testing:
-- SELECT * FROM research_history WHERE user_id = auth.uid();
-- SELECT * FROM user_profiles WHERE id = auth.uid();
-- SELECT * FROM research_summary WHERE user_id = auth.uid();

COMMENT ON TABLE research_history IS 'Stores user research sessions with agent results and performance data';
COMMENT ON TABLE user_profiles IS 'Extended user profile information and search statistics';
COMMENT ON FUNCTION update_user_search_stats IS 'Updates user search statistics after each research session';