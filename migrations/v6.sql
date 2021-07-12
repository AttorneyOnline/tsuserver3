PRAGMA foreign_keys = OFF;

-- Special ban types:
-- area_curse: ban player from all areas except one (e.g. when they connect,
--   they will be placed in a specified area and can't switch areas)
-- area_ban: ban player from a specific set of areas
ALTER TABLE bans ADD COLUMN ban_data VARCHAR;

PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;

PRAGMA user_version = 6;