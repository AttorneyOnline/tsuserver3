-- Rename room_events into area_events
CREATE TABLE area_events(
	-- event_id PRIMARY KEY, --Get rid of the primary key because longbyte fucked up and didn't make auto-increment so it was useless
	event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
	ipid INTEGER NOT NULL,
	target_ipid INTEGER,
	area_name TEXT, --Rename room_name to area_name
	char_name TEXT,
	ooc_name TEXT,
	ic_name TEXT,
  area_id INTEGER, --New
  hub_id INTEGER, --New
  hub_name TEXT, --New
	event_subtype INTEGER NOT NULL,
	message TEXT,
	FOREIGN KEY (ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (target_ipid) REFERENCES ipids(ipid)
		ON DELETE CASCADE,
	FOREIGN KEY (event_subtype) REFERENCES room_event_types(type_id)
);
-- Carry over everything we can carry over
INSERT INTO area_events (event_time, ipid, target_ipid, area_name, char_name, ooc_name, event_subtype, message)
  SELECT event_time, ipid, target_ipid, room_name, char_name, ooc_name, event_subtype, message
  FROM room_events;

DROP TABLE room_events;

-- Rename anything that has "room_" in it to "area_" for consistency
ALTER TABLE room_event_types RENAME TO area_event_types;
-- Insert into area_event_types a new chat.ic type, or IGNORE if it already exists
INSERT OR IGNORE INTO area_event_types(type_name) VALUES ("chat.ic");
-- Rename "ooc" to "chat.ooc" for consistency
UPDATE area_event_types
  SET type_name = "chat.ooc"
  WHERE type_name = "ooc";

-- Insert only columns that exist in ic_events into area_events, then add and assign the chat.ic area_event_type
INSERT INTO area_events(event_time, ipid, area_name, char_name, ic_name, message, event_subtype)
  SELECT event_time, ipid, room_name, char_name, ic_name, message, (SELECT type_id AS event_subtype FROM area_event_types WHERE type_name = "chat.ic")
  FROM ic_events;
-- Bye bye, ic_events. We no longer need you.
DROP TABLE ic_events;

-- Remove unused data from the table and try to make it smaller
VACUUM;

-- Assign the user version to 4
PRAGMA user_version = 4;