import asyncio
import sqlite3
import json

from dataclasses import dataclass
from datetime import datetime

from .exceptions import ServerError


_database_singleton = None

def __getattr__(name):
    global _database_singleton
    if _database_singleton is not None:
        _database_singleton = Database()
    return getattr(_database_singleton, name)


class Database:
    """
    Represents a connection to an SQLite database that persists
    information about the server, such as users, bans, and logs.
    """

    def __init__(self):
        self.db = sqlite3.connect('storage/db.sqlite3')
        self.db.execute('PRAGMA foreign_keys = ON')
        self.db.row_factory = sqlite3.Row

    def migrate_json_to_v1(self):
        """Migrate to v1 of the database from JSON."""
        with self.db as conn:
            with open('migrations/v1.sql', 'r') as file:
                conn.executescript(file.read())
            with open('storage/ip_ids.json', 'r') as ipids_file:
                ipids = json.loads(ipids_file.read())
                for ip, ipid in ipids:
                    conn.execute(
                        'INSERT INTO ipids(ipid, ip_address) VALUES (?, ?)',
                        (ipid, ip))
            with open('storage/hd_ids.json', 'r') as hdids_file:
                hdids = json.loads(hdids_file.read())
                for hdid, ipids in hdids:
                    for ipid in ipids:
                        conn.execute(
                            'INSERT INTO hdids(hdid, ipid) VALUES (?, ?)',
                            (hdid, ipid))
            with open('storage/banlist.json', 'r') as banlist_file:
                bans = json.load(banlist_file)
                for ipid, ban_info in bans:
                    ban = conn.execute(
                        'INSERT INTO bans(ban_id, ban_date, reason) VALUES (NULL, NULL, ?)',
                        (ban_info['Reason'], )).fetchone()
                    conn.execute(
                        'INSERT INTO ip_bans(ipid, ban_id) VALUES (?, ?)',
                        (ipid, ban['ban_id']))

    def ipid(self, ip):
        """Get an IPID from an IP address."""
        with self.db as conn:
            conn.execute(
                'INSERT OR IGNORE INTO ipids(ipid, ip) VALUES (NULL, ?)',
                (ip, ))
            return conn.execute('SELECT ipid FROM ipids WHERE ip = ?',
                                (ip, )).fetchone()['ipid']

    def add_hdid(self, ipid, hdid):
        """Associate an HDID with an IPID."""
        with self.db as conn:
            conn.execute('INSERT INTO hdids(hdid, ipid) VALUES (?, ?)',
                         (hdid, ipid))

    def ban(self,
            target_id,
            reason,
            ban_type='ipid',
            banned_by=None,
            unban_date=None,
            ban_id=None):
        """
        Ban an IPID or HDID.
        These should be used sparingly, as they can affect large swaths
        of web users if used incorrectly.
        """
        with self.db as conn:
            if ban_id is None:
                ban_id = conn.execute(
                    'INSERT INTO bans(reason, banned_by, unban_date) VALUES (?, ?, ?)',
                    (reason, banned_by.ipid, unban_date)).fetchone()['ban_id']
            if ban_type == 'ipid':
                conn.execute('INSERT INTO ip_bans(ipid, ban_id) VALUES (?, ?)',
                             (target_id, ban_id))
            elif ban_type == 'hdid':
                conn.execute(
                    'INSERT INTO hdid_bans(hdid, ban_id) VALUES (?, ?)',
                    (target_id, ban_id))
            else:
                raise ServerError(f'unknown ban type {ban_type}')

        self._schedule_unban(ban_id)
        return ban_id

    @dataclass
    class Ban:
        ban_id: int
        ban_date: datetime
        unban_date: datetime
        banned_by: str
        reason: str

    def find_ban(self, ipid, hdid):
        """Check if an IPID and/or HDID are banned."""
        with self.db as conn:
            ban = conn.execute('SELECT * FROM (SELECT ban_id FROM ip_bans WHERE ipid = ? ' +
                               'UNION SELECT ban_id FROM hdid_bans WHERE hdid = ?)' +
                               'JOIN bans USING (ban_id) LIMIT 1', (ipid, hdid)).fetchone()
            if ban is not None:
                return Database.Ban(**ban)
            else:
                return None

    def unban(self, ban_id):
        """Remove a ban entry."""
        with self.db as conn:
            unbans = conn.execute('DELETE FROM bans WHERE ban_id = ?', (ban_id,)).rowcount
            return unbans > 0

    def schedule_unbans(self):
        """
        Schedule unbans from the database.

        There is a bug in Python 3.7 and below where functions cannot be
        scheduled with a timeout longer than one day. As a workaround,
        schedule_unbans will only get the unbans for the next 12 hours
        and then will have to be called again 12 hours later.
        """
        dated_bans = []
        with self.db as conn:
            dated_bans = conn.execute('SELECT ban_id FROM bans WHERE unban_date IS NOT NULL AND ' +
                                      'datetime(unban_date) < datetime(?, \'+12 hours\')',
                                      (datetime.datetime.now(),)).fetchall()

        for ban in dated_bans:
            self._schedule_unban(ban['ban_id'])

    def _schedule_unban(self, ban_id):
        with self.db as conn:
            ban = conn.execute('SELECT unban_date FROM bans WHERE ban_id = ?', (ban_id,)).fetchone()
            time_to_unban = (ban['unban_date'] - datetime.datetime.now()).total_seconds()
            asyncio.get_event_loop().call_later(time_to_unban, self.unban, ban['ban_id'])

    def log_ic(self, client, room, showname, message):
        """Log an IC message."""
        with self.db as conn:
            conn.execute(
                'INSERT INTO ic_events(ipid, room_name, char_name, ic_name, message) VALUES (?, ?, ?, ?)',
                (client.ipid, room.abbreviation, client.char_name, showname, message))

    def log_room(self, event_subtype, client, room, message=None, target=None):
        """
        Log a room or OOC event. The event subtype is translated to an enum
        value, creating one if necessary.
        """
        ipid, char_name, ooc_name = (client.ipid, client.char_name,
                                     client.name) if client is not None else (
                                         None, None, None)
        target_ipid = target.ipid if target is not None else None
        subtype_id = self._subtype_atom('room', event_subtype)
        if isinstance(message, dict):
            message = json.dumps(message)

        with self.db as conn:
            conn.execute(
                'INSERT INTO room_events(ipid, room_name, char_name, ooc_name, ' +
                'event_subtype, message, target_ipid) VALUES (?, ?, ?, ?)',
                (ipid, room.abbreviation, char_name, ooc_name, subtype_id, message,
                target_ipid))

    def log_connect(self, client, failed=False):
        """Log a connect attempt."""
        with self.db as conn:
            conn.execute(
                'INSERT INTO connect_events(ipid, hdid, failed) VALUES (?, ?, ?)',
                (client.ipid, client.hdid, failed))

    def log_misc(self, event_subtype, client=None, target=None, data=None):
        """
        Log a miscellaneous event. The event subtype is translated to an enum
        value, creating one if necessary.
        """
        client_ipid = client.ipid if client is not None else None
        target_ipid = target.ipid if target is not None else None
        subtype_id = self._subtype_atom('misc', event_subtype)
        data_json = json.dumps(data)
        with self.db as conn:
            conn.execute(
                'INSERT INTO misc_events(ipid, target_ipid, event_subtype, event_data) VALUES (?, ?, ?, ?)',
                (client_ipid, target_ipid, subtype_id, data_json))

    def _subtype_atom(self, event_type, event_subtype):
        if event_type not in ('room', 'misc'):
            raise AssertionError()

        with self.db as conn:
            conn.execute(
                f'INSERT OR IGNORE INTO {event_type}_event_types(type_name) VALUES (?)',
                event_subtype)
            return conn.execute(
                f'SELECT type_id FROM {event_type}_event_types WHERE type_name = ?',
                event_subtype).fetchone()['type_id']
