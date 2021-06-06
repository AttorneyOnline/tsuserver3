PRAGMA foreign_keys = OFF;

ALTER TABLE hdid_bans
    RENAME TO hdid_bans_old;
CREATE TABLE hdid_bans (
    hdid    TEXT NOT NULL,
    ban_id  INTEGER NOT NULL,
    FOREIGN KEY (ban_id) REFERENCES bans(ban_id) ON DELETE CASCADE,
    PRIMARY KEY (hdid, ban_id)
);
INSERT INTO hdid_bans (hdid, ban_id) 
    SELECT hdid, ban_id 
    FROM hdid_bans_old;

ALTER TABLE ip_bans
    RENAME TO ip_bans_old;
CREATE TABLE ip_bans (
    ipid    TEXT NOT NULL,
    ban_id  INTEGER NOT NULL,
    FOREIGN KEY (ban_id) REFERENCES bans(ban_id) ON DELETE CASCADE,
    PRIMARY KEY (ipid, ban_id)
);
INSERT INTO ip_bans(ipid, ban_id)
    SELECT ipid, ban_id
    FROM ip_bans_old;

DROP TABLE ip_bans_old;
DROP TABLE hdid_bans_old;

PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;

VACUUM;

PRAGMA user_version = 5;