PRAGMA foreign_keys = OFF;

-- Remove FOREIGN KEY constraint from hdid_bans
CREATE TABLE hdid_bans_new(
	hdid TEXT PRIMARY KEY,
	ban_id INTEGER NOT NULL,
	FOREIGN KEY (ban_id) REFERENCES bans(ban_id)
		ON DELETE CASCADE
);
INSERT INTO hdid_bans_new SELECT * FROM hdid_bans;
DROP TABLE hdid_bans;
ALTER TABLE hdid_bans_new RENAME TO hdid_bans;

PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;

VACUUM;

PRAGMA user_version = 3;
