ALTER TABLE bans ADD unbanned INTEGER DEFAULT 0;

VACUUM;

PRAGMA user_version = 4;
