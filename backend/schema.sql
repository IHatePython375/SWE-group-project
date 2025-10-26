CREATE TABLE IF NOT EXISTS scores (
  id SERIAL PRIMARY KEY,
  player VARCHAR(64) NOT NULL,
  final_money INTEGER NOT NULL,
  rounds_completed INTEGER NOT NULL,
  profit INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scores_final_money ON scores(final_money DESC);