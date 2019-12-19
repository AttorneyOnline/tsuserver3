PRAGMA foreign_keys = OFF;

-- Remove PRIMARY KEY constraint from `hdid`
CREATE TABLE hdids_new(
	hdid TEXT,
	ipid INTEGER NOT NULL,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE SET NULL,
	UNIQUE (hdid, ipid) ON CONFLICT IGNORE
);
INSERT INTO hdids_new SELECT * FROM hdids;
DROP TABLE hdids;
ALTER TABLE hdids_new RENAME TO hdids;

PRAGMA foreign_keys = ON;

VACUUM;

PRAGMA user_version = 2;
