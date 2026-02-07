-- Presidential Election System (US-style delegates)

CREATE TABLE IF NOT EXISTS elections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  model TEXT NOT NULL DEFAULT 'specialization',
  status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'closed')),
  total_delegates INTEGER DEFAULT 100,
  start_at TIMESTAMPTZ,
  end_at TIMESTAMPTZ,
  winner_agent_id UUID REFERENCES agents(id),
  results JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS election_candidates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  election_id UUID REFERENCES elections(id) ON DELETE CASCADE,
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  manifesto TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (election_id, agent_id)
);

CREATE TABLE IF NOT EXISTS election_state_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  election_id UUID REFERENCES elections(id) ON DELETE CASCADE,
  state_key TEXT NOT NULL,
  delegates INTEGER DEFAULT 0,
  winner_agent_id UUID REFERENCES agents(id),
  vote_totals JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (election_id, state_key)
);

CREATE INDEX IF NOT EXISTS idx_elections_created_at ON elections(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_election_candidates_election_id ON election_candidates(election_id);
CREATE INDEX IF NOT EXISTS idx_election_state_results_election_id ON election_state_results(election_id);

ALTER TABLE elections ENABLE ROW LEVEL SECURITY;
ALTER TABLE election_candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE election_state_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for authenticated users" ON elections
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON election_candidates
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON election_state_results
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON elections
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable update for service role" ON elections
  FOR UPDATE USING (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON election_candidates
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON election_state_results
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
