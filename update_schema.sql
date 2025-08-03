-- Add new columns to research_history table for statistics
ALTER TABLE research_history 
ADD COLUMN IF NOT EXISTS completed_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS hunters_per_minute FLOAT DEFAULT 0;

-- Update existing records with default values
UPDATE research_history 
SET 
  completed_count = 0,
  hunters_per_minute = 0
WHERE completed_count IS NULL OR hunters_per_minute IS NULL;