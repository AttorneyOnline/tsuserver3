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

-- CREATE TABLE ic_events_new(
-- 	event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
-- 	ipid INTEGER NOT NULL,
-- 	area_name TEXT,
-- 	char_name TEXT,
-- 	ic_name TEXT,
-- 	message TEXT NOT NULL,
-- 	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
-- 		ON DELETE CASCADE,
-- 	FOREIGN KEY (area_name) REFERENCES area(name)
-- 		ON DELETE CASCADE
-- );
-- INSERT INTO ic_events_new 
VACUUM;

PRAGMA user_version = 3;
