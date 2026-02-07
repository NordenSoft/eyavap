-- Orchestration Engine tables

CREATE TABLE IF NOT EXISTS agent_cell_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cell_name TEXT NOT NULL,
  specialization TEXT,
  member_ids JSONB DEFAULT '[]'::jsonb,
  topic TEXT NOT NULL,
  summary TEXT NOT NULL,
  source_post_ids JSONB DEFAULT '[]'::jsonb,
  avg_consensus FLOAT DEFAULT 0.0,
  quality_score FLOAT DEFAULT 0.0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_cell_summaries_topic ON agent_cell_summaries(topic);
CREATE INDEX IF NOT EXISTS idx_agent_cell_summaries_created_at ON agent_cell_summaries(created_at DESC);

COMMENT ON TABLE agent_cell_summaries IS 'Consensus summaries produced by agent cells';
