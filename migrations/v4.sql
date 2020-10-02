-- Rename anything that has "room_" in it to "area_" for consistency
-- ALTER TABLE room_events RENAME TO area_events;
ALTER TABLE area_events RENAME COLUMN "room_name" TO "area_name";
-- Add new area_id, hub_id and hub_name information
ALTER TABLE area_events ADD "area_id" INTEGER;
ALTER TABLE area_events ADD "hub_id" INTEGER;
ALTER TABLE area_events ADD "hub_name" TEXT;

-- Rename anything that has "room_" in it to "area_" for consistency
ALTER TABLE ic_events RENAME COLUMN "room_name" TO "area_name";

-- Rename anything that has "room_" in it to "area_" for consistency
ALTER TABLE room_event_types RENAME TO area_event_types;
-- Insert into area_event_types a new chat.ic type, or IGNORE if it already exists
INSERT OR IGNORE INTO area_event_types(type_name) VALUES ('chat.ic');
-- Rename 'ooc' to 'chat.ooc' for consistency
UPDATE area_event_types
  SET type_name = 'chat.ooc'
  WHERE type_name = 'ooc';

-- ic_name did not exist in area_events until now - this is the showname
ALTER TABLE area_events ADD "ic_name" TEXT;
-- Insert only columns that exist in ic_events into area_events, then add and assign the chat.ic area_event_type
INSERT INTO area_events(event_time, ipid, area_name, char_name, ic_name, message, event_subtype)
  SELECT *, (SELECT type_id AS event_subtype FROM area_event_types WHERE type_name = 'chat.ic')
  FROM ic_events;
-- Bye bye, ic_events. We no longer need you.
DROP TABLE ic_events;

-- Longbyte nobo forgot to actually auto-increment this so the primary key is all NULL and useless, we can use event_time as primary key anyway.
-- ALTER TABLE area_events DROP COLUMN "event_id";
-- LOL SYKE SQLITE DOESN'T WORK LIKE THAT, GUESS WHAT v5 YOUR JOB WILL BE TO RECREATE *THE WHOLE TABLE* TO REMOVE *ONE COLUMN BOI* RIP IN PEACE YOU

-- Remove unused data from the table and try to make it smaller
VACUUM;

-- Assign the user version to 4
PRAGMA user_version = 4;