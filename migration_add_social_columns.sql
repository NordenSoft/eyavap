-- Migration: Agents tablosuna sosyal topluluk kolonlarını ekle
-- Bu SQL'i Supabase SQL Editor'de çalıştırın

-- 1. Agents tablosuna yeni kolonları ekle
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS ethnicity TEXT,
ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'Turkish',
ADD COLUMN IF NOT EXISTS personality_type TEXT,
ADD COLUMN IF NOT EXISTS origin_country TEXT,
ADD COLUMN IF NOT EXISTS birth_date DATE;

-- 2. Rank enum'ını güncelle (soldier eklendi)
ALTER TABLE agents
DROP CONSTRAINT IF EXISTS agents_rank_check;

ALTER TABLE agents
ADD CONSTRAINT agents_rank_check 
CHECK (rank IN ('soldier', 'specialist', 'senior_specialist', 'vice_president', 'president'));

-- 3. Mevcut ajanların rank'ini güncelle (specialist olanlar soldier olsun)
UPDATE agents
SET rank = 'soldier'
WHERE rank = 'specialist' AND merit_score < 60;

-- 4. İndeksler ekle
CREATE INDEX IF NOT EXISTS idx_agents_ethnicity ON agents(ethnicity);
CREATE INDEX IF NOT EXISTS idx_agents_language ON agents(language);

-- 5. Başkan ajanı güncelle
UPDATE agents
SET 
  ethnicity = 'Turkish',
  language = 'Turkish',
  personality_type = 'Strategic Leader',
  origin_country = 'Turkey'
WHERE id = '00000000-0000-0000-0000-000000000001';

COMMENT ON COLUMN agents.ethnicity IS 'Ajanın etnik kökeni';
COMMENT ON COLUMN agents.language IS 'Ajanın ana dili';
COMMENT ON COLUMN agents.personality_type IS 'Ajanın kişilik tipi';
COMMENT ON COLUMN agents.origin_country IS 'Ajanın menşe ülkesi';
