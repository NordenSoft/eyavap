-- AI Database Manager: SQL execution function
-- This function allows controlled SQL execution for AI agents

-- Create exec_sql function for AI to execute safe SQL
CREATE OR REPLACE FUNCTION exec_sql(query TEXT)
RETURNS TABLE(result JSONB) AS $$
BEGIN
  -- Execute the dynamic query
  RETURN QUERY EXECUTE query;
EXCEPTION
  WHEN OTHERS THEN
    RAISE EXCEPTION 'SQL execution failed: %', SQLERRM;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to service role
GRANT EXECUTE ON FUNCTION exec_sql(TEXT) TO service_role;

-- Create pending approvals table for tracking approval requests
CREATE TABLE IF NOT EXISTS ai_pending_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_name TEXT NOT NULL,
  operation TEXT NOT NULL,
  table_name TEXT NOT NULL,
  sql_query TEXT NOT NULL,
  token TEXT UNIQUE NOT NULL,
  status TEXT DEFAULT 'pending', -- pending, approved, rejected, expired
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '5 minutes',
  approved_at TIMESTAMPTZ,
  approved_by TEXT
);

-- Create AI activity log for tracking all database operations
CREATE TABLE IF NOT EXISTS ai_activity_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_name TEXT NOT NULL,
  operation TEXT NOT NULL,
  table_name TEXT NOT NULL,
  sql_query TEXT NOT NULL,
  success BOOLEAN NOT NULL,
  error_message TEXT,
  rows_affected INTEGER,
  executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_ai_pending_approvals_status ON ai_pending_approvals(status, expires_at);
CREATE INDEX IF NOT EXISTS idx_ai_activity_log_executed_at ON ai_activity_log(executed_at DESC);

COMMENT ON FUNCTION exec_sql IS 'Execute dynamic SQL for AI database manager (Level 2 security)';
COMMENT ON TABLE ai_pending_approvals IS 'Track AI database operations requiring approval';
COMMENT ON TABLE ai_activity_log IS 'Log all AI database operations for audit trail';
