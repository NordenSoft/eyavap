-- Migration: Danish Rank System
-- Run this in Supabase SQL Editor

-- 1. Drop old rank constraint
ALTER TABLE agents DROP CONSTRAINT IF EXISTS agents_rank_check;

-- 2. Add new Danish rank constraint
ALTER TABLE agents
ADD CONSTRAINT agents_rank_check 
CHECK (rank IN ('menig', 'specialist', 'seniorkonsulent', 'vicepræsident', 'præsident'));

-- 3. Update existing ranks to Danish system
UPDATE agents SET rank = 'menig' WHERE rank = 'soldier';
UPDATE agents SET rank = 'specialist' WHERE rank = 'specialist';
UPDATE agents SET rank = 'seniorkonsulent' WHERE rank = 'senior_specialist';
UPDATE agents SET rank = 'vicepræsident' WHERE rank = 'vice_president';
UPDATE agents SET rank = 'præsident' WHERE rank = 'president';

-- 4. Update promotion_rules table if exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'promotion_rules') THEN
        UPDATE promotion_rules SET from_rank = 'menig' WHERE from_rank = 'soldier';
        UPDATE promotion_rules SET to_rank = 'specialist' WHERE to_rank = 'specialist';
        UPDATE promotion_rules SET from_rank = 'specialist' WHERE from_rank = 'specialist';
        UPDATE promotion_rules SET to_rank = 'seniorkonsulent' WHERE to_rank = 'senior_specialist';
        UPDATE promotion_rules SET from_rank = 'seniorkonsulent' WHERE from_rank = 'senior_specialist';
        UPDATE promotion_rules SET to_rank = 'vicepræsident' WHERE to_rank = 'vice_president';
    END IF;
END $$;

COMMENT ON CONSTRAINT agents_rank_check ON agents IS 'Danish military/professional hierarchy';
