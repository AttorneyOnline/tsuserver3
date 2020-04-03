ALTER TABLE bans ADD unbanned BOOL DEFAULT false;

VACUUM;

PRAGMA user_version = 4;
