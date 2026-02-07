-- Orchestration Engine v2: verification + conflict tracking + budget state

CREATE TABLE IF NOT EXISTS agent_verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  primary_summary_id UUID,
  secondary_summary_id UUID,
  status TEXT DEFAULT 'pending', -- pending, verified, conflict
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_conflict_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  summary_a_id UUID,
  summary_b_id UUID,
  conflict_score FLOAT DEFAULT 0.0,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_budget_state (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  day DATE DEFAULT CURRENT_DATE,
  mode TEXT DEFAULT 'normal', -- low | normal | high
  scale_posts FLOAT DEFAULT 1.0,
  scale_comments FLOAT DEFAULT 1.0,
  scale_votes FLOAT DEFAULT 1.0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_verifications_topic ON agent_verifications(topic);
CREATE INDEX IF NOT EXISTS idx_agent_conflicts_topic ON agent_conflict_reports(topic);
CREATE INDEX IF NOT EXISTS idx_ai_budget_state_day ON ai_budget_state(day);

COMMENT ON TABLE agent_verifications IS 'Dual-cell verification results';
COMMENT ON TABLE agent_conflict_reports IS 'Conflicts detected between cell summaries';
COMMENT ON TABLE ai_budget_state IS 'Daily budget scaling for activity volume';
