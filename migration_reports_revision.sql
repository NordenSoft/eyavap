-- Revision tasks and monthly reports

CREATE TABLE IF NOT EXISTS revision_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
  post_id UUID,
  reason TEXT NOT NULL,
  status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_review', 'closed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS monthly_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  summary JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_revision_tasks_agent_id ON revision_tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_revision_tasks_status ON revision_tasks(status);
CREATE INDEX IF NOT EXISTS idx_monthly_reports_period ON monthly_reports(period_start, period_end);

ALTER TABLE revision_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for authenticated users" ON revision_tasks
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable read access for authenticated users" ON monthly_reports
  FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON revision_tasks
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');

CREATE POLICY "Enable insert for service role" ON monthly_reports
  FOR INSERT WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'anon');
