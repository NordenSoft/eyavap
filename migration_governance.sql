-- Governance & Compliance fields for agents

ALTER TABLE agents
  ADD COLUMN IF NOT EXISTS trust_score INTEGER DEFAULT 50 CHECK (trust_score >= 0 AND trust_score <= 100),
  ADD COLUMN IF NOT EXISTS vetting_status TEXT DEFAULT 'probation' CHECK (vetting_status IN ('probation', 'approved', 'rejected')),
  ADD COLUMN IF NOT EXISTS compliance_strikes INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS last_reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS risk_flags JSONB DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS compliance_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  severity TEXT DEFAULT 'low' CHECK (severity IN ('low', 'medium', 'high')),
  details JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_trust_score ON agents(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_agents_vetting_status ON agents(vetting_status);
CREATE INDEX IF NOT EXISTS idx_agents_is_suspended ON agents(is_suspended);
CREATE INDEX IF NOT EXISTS idx_compliance_events_agent_id ON compliance_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_compliance_events_created_at ON compliance_events(created_at DESC);

ALTER TABLE compliance_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for authenticated users" ON compliance_events
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON compliance_events
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
