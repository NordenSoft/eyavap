-- AI revision support for revision_tasks

ALTER TABLE revision_tasks
  ADD COLUMN IF NOT EXISTS revised_content TEXT,
  ADD COLUMN IF NOT EXISTS ai_summary TEXT;

CREATE INDEX IF NOT EXISTS idx_revision_tasks_status_created_at ON revision_tasks(status, created_at DESC);
