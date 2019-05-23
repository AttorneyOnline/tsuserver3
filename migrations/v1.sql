PRAGMA foreign_keys = ON;

-- Set `ipid` to NULL when creating an entry to auto-generate an IPID
-- When deleting an IPID, all bans and logs entries containing that
-- IPID will also be deleted to fully erase the identity of a player.
CREATE TABLE IF NOT EXISTS ipids(
	ipid INTEGER PRIMARY KEY, 
	ip_address TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS hdids(
	hdid TEXT PRIMARY KEY,
	ipid INTEGER NOT NULL,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE SET NULL,
	UNIQUE (hdid, ipid) ON CONFLICT IGNORE
);

CREATE TABLE IF NOT EXISTS ip_bans(
	ipid INTEGER PRIMARY KEY,
	ban_id INTEGER NOT NULL,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (ban_id) REFERENCES bans(ban_id)
		ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hdid_bans(
	hdid TEXT PRIMARY KEY,
	ban_id INTEGER NOT NULL,
	FOREIGN KEY (hdid) REFERENCES hdids(hdid)
		ON UPDATE CASCADE
		ON DELETE CASCADE,
	FOREIGN KEY (ban_id) REFERENCES bans(ban_id)
		ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bans(
	ban_id INTEGER PRIMARY KEY,	
	ban_date DATETIME DEFAULT CURRENT_TIMESTAMP,
	unban_date DATETIME,
	banned_by INTEGER,
	reason TEXT,
	FOREIGN KEY (banned_by) REFERENCES ipids(ipid)
		ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ic_events(
	event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	ipid INTEGER NOT NULL,
	room_name TEXT,
	char_name TEXT,
	ic_name TEXT,
	message TEXT NOT NULL,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS room_event_types(
	type_id INTEGER PRIMARY KEY,
	type_name TEXT NOT NULL UNIQUE
);

/*
INSERT INTO room_event_types(type_name) VALUES
	('ooc'),
	('wtce'),
	('penalty'),
	('roll'),
	('notecard'),
	('notecard_reveal'),
	('rolla'),
	('coinflip'),
	('blockdj'),
	('unblockdj'),
	('disemvowel'),
	('undisemvowel'),
	('shake'),
	('unshake');
*/

-- Useful for RP events and announcements, not just chat
CREATE TABLE IF NOT EXISTS room_events(
	event_id PRIMARY KEY,
	event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	ipid INTEGER NOT NULL,
	target_ipid INTEGER,
	room_name TEXT,
	char_name TEXT,
	ooc_name TEXT,
	event_subtype INTEGER NOT NULL,
	message TEXT,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (target_ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (event_subtype) REFERENCES room_event_types(type_id)
);

-- `profile_name` is NULL if the login attempt failed
CREATE TABLE IF NOT EXISTS login_events(
	event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	ipid INTEGER NOT NULL,
	profile_name TEXT,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS connect_events(
	event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	ipid INTEGER NOT NULL,
	hdid TEXT NOT NULL,
	failed INTEGER DEFAULT 0,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS misc_event_types(
	type_id INTEGER PRIMARY KEY,
	type_name TEXT NOT NULL UNIQUE
);

/*
INSERT INTO misc_event_types(type_name) VALUES
	('system'), -- server start, stop, reload
	('kick'),
	('ban'),
	('unban');
*/
	
-- Useful for system, admin, and user-defined events
CREATE TABLE IF NOT EXISTS misc_events(
	event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	ipid INTEGER, 
	target_ipid INTEGER,
	event_subtype INTEGER NOT NULL,
	event_data TEXT,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (target_ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (event_subtype) REFERENCES misc_event_types(type_id)
);

PRAGMA user_version = 1;
