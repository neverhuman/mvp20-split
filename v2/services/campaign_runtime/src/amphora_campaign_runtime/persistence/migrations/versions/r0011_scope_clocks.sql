-- Do not fabricate a clock for historical scopes at migration time.
ALTER TABLE runtime.graph_scopes ADD COLUMN opened_at timestamptz;
ALTER TABLE runtime.graph_scopes ALTER COLUMN opened_at SET DEFAULT clock_timestamp();
-- Existing column-limited UPDATE grants intentionally exclude this identity field.
