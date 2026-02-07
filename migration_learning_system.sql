-- Learning & Knowledge System

CREATE TABLE IF NOT EXISTS knowledge_units (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  source_type TEXT DEFAULT 'news',
  source_title TEXT,
  source_link TEXT,
  content TEXT NOT NULL,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],
  reliability_score NUMERIC DEFAULT 0.6 CHECK (reliability_score >= 0 AND reliability_score <= 1),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_skill_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  specialization TEXT NOT NULL,
  score NUMERIC DEFAULT 50 CHECK (score >= 0 AND score <= 100),
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (agent_id, specialization)
);

CREATE TABLE IF NOT EXISTS agent_learning_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  details JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_units_agent_id ON knowledge_units(agent_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_units_created_at ON knowledge_units(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_skill_scores_agent_id ON agent_skill_scores(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_skill_scores_specialization ON agent_skill_scores(specialization);
CREATE INDEX IF NOT EXISTS idx_agent_learning_logs_agent_id ON agent_learning_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_learning_logs_created_at ON agent_learning_logs(created_at DESC);

ALTER TABLE knowledge_units ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_skill_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_learning_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for authenticated users" ON knowledge_units
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON agent_skill_scores
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON agent_learning_logs
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON knowledge_units
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON agent_skill_scores
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable update for service role" ON agent_skill_scores
  FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON agent_learning_logs
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
