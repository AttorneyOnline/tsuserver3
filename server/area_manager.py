# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import random
import time
from enum import Enum

import yaml

from server import database
from server.evidence import EvidenceList
from server.exceptions import AreaError


class AreaManager:
    """Holds the list of all areas."""
    class Area:
        """Represents a single instance of an area."""
        def __init__(self,
                     area_id,
                     server,
                     name,
                     background,
                     bg_lock,
                     evidence_mod='FFA',
                     locking_allowed=False,
                     iniswap_allowed=True,
                     showname_changes_allowed=True,
                     shouts_allowed=True,
                     jukebox=False,
                     abbreviation='',
                     non_int_pres_only=False):
            self.iniswap_allowed = iniswap_allowed
            self.clients = set()
            self.invite_list = {}
            self.id = area_id
            self.name = name
            self.background = background
            self.bg_lock = bg_lock
            self.server = server
            self.music_looper = None
            self.next_message_time = 0
            self.hp_def = 10
            self.hp_pro = 10
            self.doc = 'No document.'
            self.status = 'IDLE'
            self.judgelog = []
            self.current_music = ''
            self.current_music_player = ''
            self.current_music_player_ipid = -1
            self.evi_list = EvidenceList()
            self.is_recording = False
            self.recorded_messages = []
            self.evidence_mod = evidence_mod
            self.locking_allowed = locking_allowed
            self.showname_changes_allowed = showname_changes_allowed
            self.shouts_allowed = shouts_allowed
            self.abbreviation = abbreviation
            self.cards = dict()
            """
            #debug
            self.evidence_list.append(Evidence("WOW", "desc", "1.png"))
            self.evidence_list.append(Evidence("wewz", "desc2", "2.png"))
            self.evidence_list.append(Evidence("weeeeeew", "desc3", "3.png"))
            """

            self.is_locked = self.Locked.FREE
            self.blankposting_allowed = True
            self.non_int_pres_only = non_int_pres_only
            self.jukebox = jukebox
            self.jukebox_votes = []
            self.jukebox_prev_char_id = -1

            self.owners = []
            self.afkers = []
            self.last_ic_message = None

        class Locked(Enum):
            """Lock state of an area."""
            FREE = 1,
            SPECTATABLE = 2,
            LOCKED = 3

        def new_client(self, client):
            """Add a client to the area."""
            self.clients.add(client)
            self.server.area_manager.send_arup_players()
            if client.char_id != -1:
                database.log_room('area.join', client, self)

        def remove_client(self, client):
            """Remove a disconnected client from the area."""
            self.clients.remove(client)
            if client in self.afkers:
                self.afkers.remove(client)
            if len(self.clients) == 0:
                self.change_status('IDLE')
            if client.char_id != -1:
                database.log_room('area.leave', client, self)

        def unlock(self):
            """Mark the area as unlocked."""
            self.is_locked = self.Locked.FREE
            self.blankposting_allowed = True
            self.invite_list = {}
            self.server.area_manager.send_arup_lock()
            self.broadcast_ooc('This area is open now.')

        def spectator(self):
            """Mark the area as spectator-only."""
            self.is_locked = self.Locked.SPECTATABLE
            for i in self.clients:
                self.invite_list[i.id] = None
            for i in self.owners:
                self.invite_list[i.id] = None
            self.server.area_manager.send_arup_lock()
            self.broadcast_ooc('This area is spectatable now.')

        def lock(self):
            """Mark the area as locked."""
            self.is_locked = self.Locked.LOCKED
            for i in self.clients:
                self.invite_list[i.id] = None
            for i in self.owners:
                self.invite_list[i.id] = None
            self.server.area_manager.send_arup_lock()
            self.broadcast_ooc('This area is locked now.')

        def is_char_available(self, char_id):
            """
            Check if a character is available for use.
            :param char_id: character ID
            """
            return char_id not in [x.char_id for x in self.clients]

        def get_rand_avail_char_id(self):
            """Get a random available character ID."""
            avail_set = set(range(len(
                self.server.char_list))) - {x.char_id
                                            for x in self.clients}
            if len(avail_set) == 0:
                raise AreaError('No available characters.')
            return random.choice(tuple(avail_set))

        def send_command(self, cmd, *args):
            """
            Broadcast an AO-compatible command to all clients in the area.
            """
            for c in self.clients:
                c.send_command(cmd, *args)

        def send_owner_command(self, cmd, *args):
            """
            Send an AO-compatible command to all owners of the area
            that are not currently in the area.
            """
            for c in self.owners:
                if c not in self.clients:
                    c.send_command(cmd, *args)

        def broadcast_ooc(self, msg):
            """
            Broadcast an OOC message to all clients in the area.
            :param msg: message
            """
            self.send_command('CT', self.server.config['hostname'], msg, '1')
            self.send_owner_command(
                'CT',
                '[' + self.abbreviation + ']' + self.server.config['hostname'],
                msg, '1')

        def set_next_msg_delay(self, msg_length):
            """
            Set the delay when the next IC message can be send by any client.
            :param msg_length: estimated length of message (ms)
            """
            delay = min(3000, 100 + 60 * msg_length)
            self.next_message_time = round(time.time() * 1000.0 + delay)

        def is_iniswap(self, client, preanim, anim, char, sfx):
            """
            Determine if a client is performing an INI swap.
            :param client: client attempting the INI swap.
            :param preanim: name of preanimation
            :param anim: name of idle/talking animation
            :param char: name of character

            """
            if self.iniswap_allowed:
                return False
            if '..' in preanim or '..' in anim or '..' in char:
                # Prohibit relative paths
                return True
            if char.lower() != client.char_name.lower():
                for char_link in self.server.allowed_iniswaps:
                    # Only allow if both the original character and the
                    # target character are in the allowed INI swap list
                    if client.char_name in char_link and char in char_link:
                        return False
            return not self.server.char_emotes[char].validate(preanim, anim, sfx)

        def add_jukebox_vote(self, client, music_name, length=-1, showname=''):
            """
            Cast a vote on the jukebox.
            :param music_name: track name
            :param length: length of track (Default value = -1)
            :param showname: showname of voter (?) (Default value = '')
            """
            if not self.jukebox:
                return
            if length <= 0:
                self.remove_jukebox_vote(client, False)
            else:
                self.remove_jukebox_vote(client, True)
                self.jukebox_votes.append(
                    self.JukeboxVote(client, music_name, length, showname))
                client.send_ooc('Your song was added to the jukebox.')
                if len(self.jukebox_votes) == 1:
                    self.start_jukebox()

        def remove_jukebox_vote(self, client, silent):
            """
            Removes a vote on the jukebox.
            :param client: client whose vote should be removed
            :param silent: do not notify client

            """
            if not self.jukebox:
                return
            for current_vote in self.jukebox_votes:
                if current_vote.client.id == client.id:
                    self.jukebox_votes.remove(current_vote)
            if not silent:
                client.send_ooc(
                    'You removed your song from the jukebox.')

        def get_jukebox_picked(self):
            """Randomly choose a track from the jukebox."""
            if not self.jukebox:
                return
            if len(self.jukebox_votes) == 0:
                return None
            elif len(self.jukebox_votes) == 1:
                return self.jukebox_votes[0]
            else:
                weighted_votes = []
                for current_vote in self.jukebox_votes:
                    i = 0
                    while i < current_vote.chance:
                        weighted_votes.append(current_vote)
                        i += 1
                return random.choice(weighted_votes)

        def start_jukebox(self):
            """Initialize jukebox mode if needed and play the next track."""
            # There is a probability that the jukebox feature has been turned off since then,
            # we should check that.
            # We also do a check if we were the last to play a song, just in case.
            if not self.jukebox:
                if self.current_music_player == 'The Jukebox' and self.current_music_player_ipid == 'has no IPID':
                    self.current_music = ''
                return

            vote_picked = self.get_jukebox_picked()

            if vote_picked is None:
                self.current_music = ''
                return

            if vote_picked.client.char_id != self.jukebox_prev_char_id or vote_picked.name != self.current_music or len(
                    self.jukebox_votes) > 1:
                self.jukebox_prev_char_id = vote_picked.client.char_id
                if vote_picked.showname == '':
                    self.send_command('MC', vote_picked.name,
                                      vote_picked.client.char_id)
                else:
                    self.send_command('MC', vote_picked.name,
                                      vote_picked.client.char_id,
                                      vote_picked.showname)
            else:
                self.send_command('MC', vote_picked.name, -1)

            self.current_music_player = 'The Jukebox'
            self.current_music_player_ipid = 'has no IPID'
            self.current_music = vote_picked.name

            for current_vote in self.jukebox_votes:
                # Choosing the same song will get your votes down to 0, too.
                # Don't want the same song twice in a row!
                if current_vote.name == vote_picked.name:
                    current_vote.chance = 0
                else:
                    current_vote.chance += 1

            if self.music_looper:
                self.music_looper.cancel()
            self.music_looper = asyncio.get_event_loop().call_later(
                vote_picked.length, lambda: self.start_jukebox())

        def play_music(self, name, cid, loop=0, showname="", effects=0):
            """
            Play a track.
            :param name: track name
            :param cid: origin character ID
            :param loop: 1 for clientside looping, 0 for no looping (2.8)
            :param showname: showname of origin user
            :param effects: fade out/fade in/sync/etc. effect bitflags
            """
            # If it's anything other than 0, it's looping. (Legacy music.yaml support)
            if loop != 0:
                loop = 1
            self.send_command('MC', name, cid, showname, loop, 0, effects)

        def can_send_message(self, client):
            """
            Check if a client can send an IC message in this area.
            :param client: sender
            """
            if self.cannot_ic_interact(client):
                client.send_ooc(
                    'This is a locked area - ask the CM to speak.')
                return False
            return (time.time() * 1000.0 - self.next_message_time) > 0

        def cannot_ic_interact(self, client):
            """
            Check if this room is locked to a client.
            :param client: sender
            """
            return self.is_locked != self.Locked.FREE and not client.is_mod and not client.id in self.invite_list

        def change_hp(self, side, val):
            """
            Set the penalty bars.
            :param side: 1 for defense; 2 for prosecution
            :param val: value from 0 to 10
            """
            if not 0 <= val <= 10:
                raise AreaError('Invalid penalty value.')
            if not 1 <= side <= 2:
                raise AreaError('Invalid penalty side.')
            if side == 1:
                self.hp_def = val
            elif side == 2:
                self.hp_pro = val
            self.send_command('HP', side, val)

        def change_background(self, bg):
            """
            Set the background.
            :param bg: background name
            :raises: AreaError if `bg` is not in background list
            """
            if bg.lower() not in (name.lower()
                                  for name in self.server.backgrounds):
                raise AreaError('Invalid background name.')
            self.background = bg
            self.send_command('BN', self.background)

        def change_status(self, value):
            """
            Set the status of the room.
            :param value: status code
            """
            allowed_values = ('idle', 'rp', 'casing', 'looking-for-players',
                              'lfp', 'recess', 'gaming')
            if value.lower() not in allowed_values:
                raise AreaError(
                    f'Invalid status. Possible values: {", ".join(allowed_values)}'
                )
            if value.lower() == 'lfp':
                value = 'looking-for-players'
            self.status = value.upper()
            self.server.area_manager.send_arup_status()

        def change_doc(self, doc='No document.'):
            """
            Set the doc link.
            :param doc: doc link (Default value = 'No document.')
            """
            self.doc = doc

        def add_to_judgelog(self, client, msg):
            """
            Append an event to the judge log (max 10 items).
            :param client: event origin
            :param msg: event message
            """
            if len(self.judgelog) >= 10:
                self.judgelog = self.judgelog[1:]
            self.judgelog.append(
                f'{client.char_name} ({client.ip}) {msg}.')

        def add_music_playing(self, client, name, showname=''):
            """
            Set info about the current track playing.
            :param client: player
            :param showname: showname of player (can be blank)
            :param name: track name
            """
            if showname != '':
                self.current_music_player = f'{showname} ({client.char_name})'
            else:
                self.current_music_player = client.char_name
            self.current_music_player_ipid = client.ipid
            self.current_music = name

        def get_evidence_list(self, client):
            """
            Get the evidence list of the area.
            :param client: requester
            """
            client.evi_list, evi_list = self.evi_list.create_evi_list(client)
            return evi_list

        def broadcast_evidence_list(self):
            """
            Broadcast an updated evidence list.
            LE#<name>&<desc>&<img>#<name>
            """
            for client in self.clients:
                client.send_command('LE', *self.get_evidence_list(client))

        def get_cms(self):
            """
            Get a list of CMs.
            :return: message
            """
            msg = ''
            for i in self.owners:
                msg += f'[{str(i.id)}] {i.char_name}, '
            if len(msg) > 2:
                msg = msg[:-2]
            return msg

        class JukeboxVote:
            """Represents a single vote cast for the jukebox."""
            def __init__(self, client, name, length, showname):
                self.client = client
                self.name = name
                self.length = length
                self.chance = 1
                self.showname = showname

    def __init__(self, server):
        self.server = server
        self.cur_id = 0
        self.areas = []
        self.load_areas()

    def load_areas(self):
        """Create all areas from a YAML file."""
        with open('config/areas.yaml', 'r') as chars:
            areas = yaml.safe_load(chars)
        for item in areas:
            if 'evidence_mod' not in item:
                item['evidence_mod'] = 'FFA'
            if 'locking_allowed' not in item:
                item['locking_allowed'] = False
            if 'iniswap_allowed' not in item:
                item['iniswap_allowed'] = True
            if 'showname_changes_allowed' not in item:
                item['showname_changes_allowed'] = True
            if 'shouts_allowed' not in item:
                item['shouts_allowed'] = True
            if 'jukebox' not in item:
                item['jukebox'] = False
            if 'noninterrupting_pres' not in item:
                item['noninterrupting_pres'] = False
            if 'abbreviation' not in item:
                item['abbreviation'] = self.abbreviate(
                    item['area'])
            self.areas.append(
                self.Area(self.cur_id, self.server, item['area'],
                          item['background'], item['bglock'],
                          item['evidence_mod'], item['locking_allowed'],
                          item['iniswap_allowed'],
                          item['showname_changes_allowed'],
                          item['shouts_allowed'], item['jukebox'],
                          item['abbreviation'], item['noninterrupting_pres']))
            self.cur_id += 1

    def default_area(self):
        """Get the default area."""
        return self.areas[0]

    def get_area_by_name(self, name):
        """Get an area by name."""
        for area in self.areas:
            if area.name == name:
                return area
        raise AreaError('Area not found.')

    def get_area_by_id(self, num):
        """Get an area by ID."""
        for area in self.areas:
            if area.id == num:
                return area
        raise AreaError('Area not found.')

    def abbreviate(self, name):
        """Abbreviate the name of a room."""
        if name.lower().startswith("courtroom"):
            return "CR" + name.split()[-1]
        elif name.lower().startswith("area"):
            return "A" + name.split()[-1]
        elif len(name.split()) > 1:
            return "".join(item[0].upper() for item in name.split())
        elif len(name) > 3:
            return name[:3].upper()
        else:
            return name.upper()

    def send_remote_command(self, area_ids, cmd, *args):
        """
        Broadcast an AO-compatible command to a specified
        list of areas and their owners.
        :param area_ids: list of area IDs
        :param cmd: command name
        :param *args: command arguments
        """
        for a_id in area_ids:
            self.get_area_by_id(a_id).send_command(cmd, *args)
            self.get_area_by_id(a_id).send_owner_command(cmd, *args)

    def send_arup_players(self):
        """Broadcast ARUP packet containing player counts."""
        players_list = [0]
        for area in self.areas:
            players_list.append(len(area.clients))
        self.server.send_arup(players_list)

    def send_arup_status(self):
        """Broadcast ARUP packet containing area statuses."""
        status_list = [1]
        for area in self.areas:
            status_list.append(area.status)
        self.server.send_arup(status_list)

    def send_arup_cms(self):
        """Broadcast ARUP packet containing area CMs."""
        cms_list = [2]
        for area in self.areas:
            cm = 'FREE'
            if len(area.owners) > 0:
                cm = area.get_cms()
            cms_list.append(cm)
        self.server.send_arup(cms_list)

    def send_arup_lock(self):
        """Broadcast ARUP packet containing the lock status of each area."""
        lock_list = [3]
        for area in self.areas:
            lock_list.append(area.is_locked.name)
        self.server.send_arup(lock_list)
