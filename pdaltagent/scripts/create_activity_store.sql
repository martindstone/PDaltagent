BEGIN TRANSACTION;
CREATE TABLE log_entries (
				id TEXT NOT NULL,
				created_at timestamp);
COMMIT;