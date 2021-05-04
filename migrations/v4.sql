PRAGMA foreign_keys = OFF;

-- Remove FOREIGN KEY constraint from ip_bans
CREATE TABLE ip_bans_new(
	ipid TEXT PRIMARY KEY,
	ban_id INTEGER NOT NULL,
	FOREIGN KEY (ban_id) REFERENCES bans(ban_id)
		ON DELETE CASCADE
);
INSERT INTO ip_bans_new SELECT * FROM ip_bans;
DROP TABLE ip_bans;
ALTER TABLE ip_bans_new RENAME TO ip_bans;

-- Add unbanned column
ALTER TABLE bans ADD unbanned INTEGER DEFAULT 0;

PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;

VACUUM;

PRAGMA user_version = 4;
