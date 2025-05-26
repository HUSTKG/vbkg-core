CREATE TABLE IF NOT EXISTS rate_limiter_logs (
	id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
	identifier TEXT NOT NULL,
	scope TEXT NOT NULL,
	allowed BOOLEAN NOT NULL,
	limit_value INTEGER NOT NULL,
	remaining INTEGER NOT NULL,
	timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_rate_limiter_identifier ON rate_limiter_logs(identifier);
CREATE INDEX IF NOT EXISTS idx_rate_limiter_scope ON rate_limiter_logs(scope);
CREATE INDEX IF NOT EXISTS idx_rate_limiter_timestamp ON rate_limiter_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_rate_limiter_identifier_scope ON rate_limiter_logs(identifier, scope);

