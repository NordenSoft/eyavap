-- EYAVAP: Ajan Sistemi Veritabanı Şeması
-- Bu SQL dosyasını Supabase SQL Editor'de çalıştırın

-- 1. Ajanlar Tablosu
CREATE TABLE IF NOT EXISTS agents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  specialization TEXT NOT NULL,
  expertise_areas TEXT[] NOT NULL,
  capabilities TEXT[] DEFAULT ARRAY['research', 'analysis', 'reporting'],
  merit_score INTEGER DEFAULT 50 CHECK (merit_score >= 0 AND merit_score <= 100),
  rank TEXT DEFAULT 'specialist' CHECK (rank IN ('specialist', 'senior_specialist', 'vice_president', 'president')),
  total_queries INTEGER DEFAULT 0,
  successful_queries INTEGER DEFAULT 0,
  failed_queries INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_used TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- 2. Ajan Sorguları Tablosu
CREATE TABLE IF NOT EXISTS agent_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  user_query TEXT NOT NULL,
  agent_response TEXT,
  user_feedback INTEGER CHECK (user_feedback >= 1 AND user_feedback <= 5),
  execution_time_ms INTEGER,
  actions_taken JSONB DEFAULT '[]'::jsonb,
  success BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Başkan Yardımcısı Kurulu Tablosu
CREATE TABLE IF NOT EXISTS vice_president_council (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  appointed_at TIMESTAMPTZ DEFAULT NOW(),
  term_start TIMESTAMPTZ DEFAULT NOW(),
  term_end TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  UNIQUE(agent_id)
);

-- 4. Eylem Logları Tablosu (siber araştırma, sistem etkileşimi)
CREATE TABLE IF NOT EXISTS action_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  query_id UUID REFERENCES agent_queries(id) ON DELETE CASCADE,
  action_type TEXT NOT NULL CHECK (action_type IN ('web_search', 'api_call', 'data_analysis', 'system_interaction', 'research')),
  action_details JSONB NOT NULL,
  result JSONB,
  success BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- İndeksler (Performans için)
CREATE INDEX IF NOT EXISTS idx_agents_specialization ON agents(specialization);
CREATE INDEX IF NOT EXISTS idx_agents_merit_score ON agents(merit_score DESC);
CREATE INDEX IF NOT EXISTS idx_agents_rank ON agents(rank);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_agent_queries_agent_id ON agent_queries(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_queries_created_at ON agent_queries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_action_logs_agent_id ON action_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_action_logs_action_type ON action_logs(action_type);

-- RLS (Row Level Security) Politikaları
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_queries ENABLE ROW LEVEL SECURITY;
ALTER TABLE vice_president_council ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_logs ENABLE ROW LEVEL SECURITY;

-- Herkese okuma izni (authenticated users için)
CREATE POLICY "Enable read access for authenticated users" ON agents
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON agent_queries
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON vice_president_council
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON action_logs
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

-- Yazma izni (servis rolü için)
CREATE POLICY "Enable insert for service role" ON agents
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable update for service role" ON agents
  FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON agent_queries
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable update for service role" ON agent_queries
  FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON vice_president_council
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable update for service role" ON vice_president_council
  FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON action_logs
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

-- Trigger: Ajan liyakat puanını otomatik güncelle
CREATE OR REPLACE FUNCTION update_agent_merit_score()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE agents
  SET 
    merit_score = LEAST(100, GREATEST(0, 
      50 + (successful_queries * 2) - (failed_queries * 3)
    )),
    total_queries = total_queries + 1,
    successful_queries = successful_queries + CASE WHEN NEW.success THEN 1 ELSE 0 END,
    failed_queries = failed_queries + CASE WHEN NOT NEW.success THEN 1 ELSE 0 END,
    last_used = NOW()
  WHERE id = NEW.agent_id;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_merit_score
AFTER INSERT ON agent_queries
FOR EACH ROW
EXECUTE FUNCTION update_agent_merit_score();

-- Trigger: Başkan Yardımcısı otomatik ataması (merit_score >= 85)
CREATE OR REPLACE FUNCTION promote_to_vice_president()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.merit_score >= 85 AND NEW.rank = 'senior_specialist' THEN
    UPDATE agents
    SET rank = 'vice_president'
    WHERE id = NEW.id;
    
    INSERT INTO vice_president_council (agent_id)
    VALUES (NEW.id)
    ON CONFLICT (agent_id) DO NOTHING;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_promote_to_vice_president
AFTER UPDATE ON agents
FOR EACH ROW
WHEN (NEW.merit_score >= 85)
EXECUTE FUNCTION promote_to_vice_president();

-- Başlangıç Verisi: Başkan Ajan
INSERT INTO agents (
  id,
  name,
  specialization,
  expertise_areas,
  capabilities,
  merit_score,
  rank,
  is_active
) VALUES (
  '00000000-0000-0000-0000-000000000001',
  'Başkan Ajan',
  'orchestration',
  ARRAY['coordination', 'delegation', 'decision_making', 'system_architecture'],
  ARRAY['orchestrate', 'delegate', 'create_agents', 'evaluate', 'research', 'analysis', 'reporting'],
  100,
  'president',
  TRUE
) ON CONFLICT DO NOTHING;

-- View: Ajan İstatistikleri
CREATE OR REPLACE VIEW agent_statistics AS
SELECT 
  a.id,
  a.name,
  a.specialization,
  a.rank,
  a.merit_score,
  a.total_queries,
  a.successful_queries,
  a.failed_queries,
  CASE 
    WHEN a.total_queries > 0 
    THEN ROUND((a.successful_queries::numeric / a.total_queries::numeric) * 100, 2)
    ELSE 0 
  END AS success_rate,
  COUNT(DISTINCT aq.id) AS queries_last_7_days,
  a.last_used,
  a.created_at
FROM agents a
LEFT JOIN agent_queries aq ON a.id = aq.agent_id AND aq.created_at > NOW() - INTERVAL '7 days'
GROUP BY a.id, a.name, a.specialization, a.rank, a.merit_score, a.total_queries, a.successful_queries, a.failed_queries, a.last_used, a.created_at;

-- View: Başkan Yardımcısı Kurulu
CREATE OR REPLACE VIEW active_vice_presidents AS
SELECT 
  vp.id AS council_id,
  a.id AS agent_id,
  a.name,
  a.specialization,
  a.merit_score,
  a.total_queries,
  vp.appointed_at,
  vp.term_start
FROM vice_president_council vp
JOIN agents a ON vp.agent_id = a.id
WHERE vp.is_active = TRUE
ORDER BY a.merit_score DESC;

COMMENT ON TABLE agents IS 'Tüm yapay zeka ajanlarının kayıtları';
COMMENT ON TABLE agent_queries IS 'Ajanlara yapılan sorgu ve cevap kayıtları';
COMMENT ON TABLE vice_president_council IS 'Başkan Yardımcısı Kurulu üyeleri';
COMMENT ON TABLE action_logs IS 'Ajanların gerçekleştirdiği eylem logları';
