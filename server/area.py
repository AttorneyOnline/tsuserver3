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

import oyaml as yaml #ordered yaml
import os

from server import database
from server.evidence import EvidenceList
from server.exceptions import AreaError
from server.constants import MusicEffect

from collections import OrderedDict

class Area:
    """Represents a single instance of an area."""
    def __init__(self,
                    area_manager,
                    name):
        self.clients = set()
        self.invite_list = set()
        self.area_manager = area_manager
        self._name = name

        # Initialize prefs
        self.background = 'default'
        self.pos_lock = []
        self.bg_lock = False
        self.evidence_mod = 'FFA'
        self.can_cm = False
        self.locking_allowed = False
        self.iniswap_allowed = True
        self.showname_changes_allowed = True
        self.shouts_allowed = True
        self.jukebox = False
        self.abbreviation = self.abbreviate()
        self.non_int_pres_only = False
        self.is_locked = self.Locked.FREE
        self.blankposting_allowed = True
        self.hp_def = 10
        self.hp_pro = 10
        self.doc = 'No document.'
        self.status = 'IDLE'
        self.move_delay = 0
        self.hide_clients = False
        self.max_players = -1
        self.desc = ''
        self.music_ref = ''
        self.music_override = False
        self.replace_music = False
        self.ambience = ''
        self.can_dj = True
        self.hidden = False
        # /prefs end

        self.music_looper = None
        self.next_message_time = 0
        self.judgelog = []
        self.current_music = ''
        self.current_music_player = ''
        self.current_music_player_ipid = -1
        self.current_music_looping = 0
        self.current_music_effects = 0
        self.music_autoplay = False
        self.evi_list = EvidenceList()
        self.recorded_messages = []
        self.cards = dict()
        """
        #debug
        self.evidence_list.append(Evidence("WOW", "desc", "1.png"))
        self.evidence_list.append(Evidence("wewz", "desc2", "2.png"))
        self.evidence_list.append(Evidence("weeeeeew", "desc3", "3.png"))
        """

        self.jukebox_votes = []
        self.jukebox_prev_char_id = -1

        self.music_list = []

        self._owners = set()
        self.afkers = []

        # Dictionary of dictionaries with further info, examine def link for more info
        self.links = {}

    class Locked(Enum):
        """Lock state of an area."""
        FREE = 1,
        SPECTATABLE = 2,
        LOCKED = 3

    @property
    def name(self):
        """Area's name string. Abbreviation is also updated according to this."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.abbreviation = self.abbreviate()

    @property
    def id(self):
        """Get area's index in the AreaManager's 'areas' list."""
        return self.area_manager.areas.index(self)

    @property
    def server(self):
        """Area's server. Accesses AreaManager's 'server' property"""
        return self.area_manager.server

    @property
    def owners(self):
        """Area's owners. Also appends Game Masters (Hub Managers)."""
        return self.area_manager.owners | self._owners

    def abbreviate(self):
        """Abbreviate our name."""
        if self.name.lower().startswith("courtroom"):
            return "CR" + self.name.split()[-1]
        elif self.name.lower().startswith("area"):
            return "A" + self.name.split()[-1]
        elif len(self.name.split()) > 1:
            return "".join(item[0].upper() for item in self.name.split())
        elif len(self.name) > 3:
            return self.name[:3].upper()
        else:
            return self.name.upper()

    def load(self, area):
        self._name = area['area']
        if 'background' in area:
            self.background = area['background']
        _pos_lock = ''
        # Legacy KFO support.
        # We gotta fix the sins of our forefathers
        if 'poslock' in area:
            _pos_lock = area['poslock'].split(' ')
        if 'bglock' in area:
            self.bg_lock = area['bglock']
        if 'accessible' in area:
            self.links.clear()
            for link in [s for s in str(area['accessible']).split(' ')]:
                self.link(link)

        if 'locked' in area:
            self.is_locked = self.Locked.FREE
            if area['locked'] == True:
                self.is_locked = self.Locked.LOCKED

        if 'bg_lock' in area:
            self.bg_lock = area['bg_lock']
        if 'pos_lock' in area:
            _pos_lock = area['pos_lock'].split(' ')

        if len(_pos_lock) > 0:
            self.pos_lock.clear()
            for pos in _pos_lock:
                pos = pos.lower()
                if pos != "none" and not (pos in self.pos_lock):
                    self.pos_lock.append(pos)

        if 'evidence_mod' in area:
            self.evidence_mod = area['evidence_mod']
        if 'can_cm' in area:
            self.can_cm = area['can_cm']
        if 'locking_allowed' in area:
            self.locking_allowed = area['locking_allowed']
        if 'iniswap_allowed' in area:
            self.iniswap_allowed = area['iniswap_allowed']
        if 'showname_changes_allowed' in area:
            self.showname_changes_allowed = area['showname_changes_allowed']
        if 'shouts_allowed' in area:
            self.shouts_allowed = area['shouts_allowed']
        if 'jukebox' in area:
            self.jukebox = area['jukebox']
        if 'abbreviation' in area:
            self.abbreviation = area['abbreviation']
        else:
            self.abbreviation = self.abbreviate()
        if 'non_int_pres_only' in area:
            self.non_int_pres_only = area['non_int_pres_only']
        if 'is_locked' in area:
            self.is_locked = self.Locked[area['is_locked']]
        if 'blankposting_allowed' in area:
            self.blankposting_allowed = area['blankposting_allowed']
        if 'hp_def' in area:
            self.hp_def = area['hp_def']
        if 'hp_pro' in area:
            self.hp_pro = area['hp_pro']
        if 'doc' in area:
            self.doc = area['doc']
        if 'status' in area:
            self.status = area['status']
        if 'move_delay' in area:
            self.move_delay = area['move_delay']
        if 'hide_clients' in area:
            self.hide_clients = area['hide_clients']
        if 'music_autoplay' in area:
            self.music_autoplay = area['music_autoplay']
            if self.music_autoplay and 'music' in area:
                self.current_music = area['music']
        if 'max_players' in area:
            self.max_players = area['max_players']
        if 'desc' in area:
            self.desc = area['desc']
        if 'music_ref' in area:
            self.clear_music()
            self.music_ref = area['music_ref']
        if self.music_ref != '':
            self.load_music(f'storage/musiclists/{self.music_ref}.yaml')
            
        if 'music_override' in area:
            self.music_override = area['music_override']
        if 'replace_music' in area:
            self.replace_music = area['replace_music']
        if 'ambience' in area:
            self.ambience = area['ambience']
        if 'can_dj' in area:
            self.can_dj = area['can_dj']
        if 'hidden' in area:
            self.hidden = area['hidden']

        if 'evidence' in area and len(area['evidence']) > 0:
            self.evi_list.evidences.clear()
            self.evi_list.import_evidence(area['evidence'])
            self.broadcast_evidence_list()

        if 'links' in area and len(area['links']) > 0:
            self.links = area['links']

    def save(self):
        area = OrderedDict()
        area['area'] = self.name
        area['background'] = self.background
        if len(self.pos_lock) > 0:
            area['pos_lock'] = ' '.join(map(str, self.pos_lock))
        area['bg_lock'] = self.bg_lock
        area['evidence_mod'] = self.evidence_mod
        area['can_cm'] = self.can_cm
        area['locking_allowed'] = self.locking_allowed
        area['iniswap_allowed'] = self.iniswap_allowed
        area['showname_changes_allowed'] = self.showname_changes_allowed
        area['shouts_allowed'] = self.shouts_allowed
        area['jukebox'] = self.jukebox
        area['abbreviation'] = self.abbreviation
        area['non_int_pres_only'] = self.non_int_pres_only
        area['is_locked'] = self.is_locked.name
        area['blankposting_allowed'] = self.blankposting_allowed
        area['hp_def'] = self.hp_def
        area['hp_pro'] = self.hp_pro
        area['doc'] = self.doc
        area['status'] = self.status
        area['move_delay'] = self.move_delay
        area['hide_clients'] = self.hide_clients
        area['music_autoplay'] = self.music_autoplay
        area['max_players'] = self.max_players
        area['desc'] = self.desc
        if self.music_ref != '':
            area['music_ref'] = self.music_ref
            area['replace_music'] = self.replace_music
        area['music_override'] = self.music_override
        if self.music_autoplay:
            area['music'] = self.current_music
        area['ambience'] = self.ambience
        area['can_dj'] = self.can_dj
        area['hidden'] = self.hidden
        if len(self.evi_list.evidences) > 0:
            area['evidence'] = [e.to_dict() for e in self.evi_list.evidences]
        if len(self.links) > 0:
            area['links'] = self.links
        return area

    def new_client(self, client):
        """Add a client to the area."""
        self.clients.add(client)
        if client.char_id != -1:
            database.log_room('area.join', client, self)
            if self.music_autoplay:
                client.send_command('MC', self.current_music, -1, '', self.current_music_looping, 0, self.current_music_effects)

            # Play the ambience
            self.send_command('MC', self.ambience, -1, "", 1, 1, int(MusicEffect.FADE_OUT | MusicEffect.FADE_IN | MusicEffect.SYNC_POS))

    def remove_client(self, client):
        """Remove a disconnected client from the area."""
        self.clients.remove(client)
        if client in self.afkers:
            self.afkers.remove(client)
            self.server.client_manager.toggle_afk(client)
        if self.jukebox:
            self.remove_jukebox_vote(client, True)
        if len(self.clients) == 0:
            self.change_status('IDLE')
        if client.char_id != -1:
            database.log_room('area.leave', client, self)

        # Update everyone's available characters list
        self.send_command('CharsCheck',
                            *client.get_available_char_list())

    def unlock(self):
        """Mark the area as unlocked."""
        self.is_locked = self.Locked.FREE
        self.blankposting_allowed = True
        self.invite_list.clear()
        self.area_manager.send_arup_lock()

    def spectator(self):
        """Mark the area as spectator-only."""
        self.is_locked = self.Locked.SPECTATABLE
        self.area_manager.send_arup_lock()

    def lock(self):
        """Mark the area as locked."""
        self.is_locked = self.Locked.LOCKED
        self.area_manager.send_arup_lock()
    
    def link(self, target, locked=False, hidden=False, target_pos='', can_peek=True):
        """
        Sets up a one-way connection between this area and targeted area.
        Returns the link dictionary.
        :param target: the targeted Area ID to connect
        :param locked: is the link unusable?
        :param hidden: is the link  invisible?
        :param target_pos: which position should we end up in when we come through
        :param can_peek: can you peek through this path?

        """
        link = {
            "locked": locked,
            "hidden": hidden,
            "target_pos": target_pos,
            "can_peek": can_peek,
        }
        self.links[str(target)] = link
        return link

    def unlink(self, target):
        try:
            del self.links[str(target)]
        except KeyError:
            raise AreaError(f'Link {target} does not exist in Area {self.name}!')

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
            if c not in self.clients and \
              (c.remote_listen == 3 or \
              (cmd == 'CT' and c.remote_listen == 2) or \
              (cmd == 'MS' and c.remote_listen == 1)):
                c.send_command(cmd, *args)

    def broadcast_ooc(self, msg):
        """
        Broadcast an OOC message to all clients in the area.
        :param msg: message
        """
        self.send_command('CT', self.server.config['hostname'], msg, '1')
        self.send_owner_command(
            'CT',
            '[' + self.abbreviation + '] ' + self.server.config['hostname'],
            msg, '1')
    
    def send_ic(self, client, *args):
        """
        Send an IC message from a client to all applicable clients in the area.
        :param client: speaker
        :param *args: arguments
        """
        if client in self.afkers:
            client.server.client_manager.toggle_afk(client)
        if client.hidden_in != None:
            client.hide(False)
        for c in self.clients:
            # Blinded clients don't receive IC messages
            if c.blinded:
                continue
            # pos doesn't match listen_pos, we're not listening so make this an OOC message instead
            if c.listen_pos != None:
                if type(c.listen_pos) is list and not (args[5] in c.listen_pos) or \
                    c.listen_pos == 'self' and args[5] != c.pos:
                    name = client.name
                    if args[8] != -1:
                        name = self.server.char_list[args[8]]
                    if args[15] != '':
                        name = args[15]
                    # Send the mesage as OOC.
                    # Woulda been nice if there was a packet to send messages to IC log
                    # without displaying it in the viewport.
                    c.send_command('CT', f'[pos \'{args[5]}\'] {name}', args[4])
                    continue
            c.send_command('MS', *args)

        # args[4] = msg
        # args[15] = showname
        name = client.name
        if args[8] != -1:
            name = self.server.char_list[args[8]]
        if args[15] != '':
            name = args[15]
        client.area.set_next_msg_delay(len(args[4]))
        database.log_ic(client, client.area, name, args[4])

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

    def clear_music(self):
        self.music_list.clear()
        self.music_ref = ''

    def load_music(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as stream:
                self.music_list = yaml.safe_load(stream)

            prepath = ''
            for item in self.music_list:
                # deprecated, use 'replace_music' area pref instead
                # if 'replace' in item:
                #     self.replace_music = item['replace'] == True
                if 'use_unique_folder' in item and item['use_unique_folder'] == True:
                    prepath = os.path.splitext(os.path.basename(path))[0] + '/'

                if 'category' not in item:
                    continue
                
                if 'songs' in item:
                    for song in item['songs']:
                        song['name'] = prepath + song['name']
        except ValueError:
            raise
        except AreaError:
            raise

    def add_jukebox_vote(self, client, music_name, length=-1, showname=''):
        """
        Cast a vote on the jukebox.
        :param music_name: track name
        :param length: length of track (Default value = -1)
        :param showname: showname of voter (?) (Default value = '')
        """
        if not self.jukebox:
            return
        if length == 0:
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

    def set_ambience(self, name):
        self.ambience = name
        self.send_command('MC', self.ambience, -1, "", 1, 1, int(MusicEffect.FADE_OUT | MusicEffect.FADE_IN | MusicEffect.SYNC_POS))

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
        self.current_music_looping = loop
        self.current_music_effects = effects
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
        return self.is_locked == self.Locked.SPECTATABLE and not client.is_mod and not client.id in self.invite_list and not client.id in self.owners

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
        if self.server.use_backgrounds_yaml and bg.lower() not in (name.lower()
                                for name in self.server.backgrounds):
            raise AreaError('Invalid background name.')
        self.background = bg
        for client in self.clients:
            #Update all clients to the pos lock
            if len(self.pos_lock) > 0 and client.pos not in self.pos_lock:
                client.change_position(self.pos_lock[0])
            client.send_command('BN', self.background, client.pos)

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
        self.area_manager.send_arup_status()

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

    def add_music_playing(self, client, name, showname='', autoplay=None):
        """
        Set info about the current track playing.
        :param client: player
        :param showname: showname of player (can be blank)
        :param name: track name
        :param autoplay: if track will play itself as soon as user joins area
        """
        if showname != '':
            self.current_music_player = f'{showname} ({client.char_name})'
        else:
            self.current_music_player = client.char_name
        self.current_music_player_ipid = client.ipid
        self.current_music = name
        if autoplay == None:
            autoplay = self.music_autoplay
        self.music_autoplay = autoplay

    def get_evidence_list(self, client):
        """
        Get the evidence list of the area.
        :param client: requester
        """
        client.evi_list, evi_list = self.evi_list.create_evi_list(client)
        if client.blinded:
            return [0]
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

    def add_owner(self, client):
        """
        Add a CM to the area.
        """
        self._owners.add(client)

        # Make sure the client's available areas are updated
        self.broadcast_area_list(client)

        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA
        # This should be remade by only sending updates to those players
        # who would actually be affected, and all players who don't need
        # an update are ignored.
        self.area_manager.send_arup_players()
        self.area_manager.send_arup_status()
        self.area_manager.send_arup_cms()
        self.area_manager.send_arup_lock()
        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA

        self.broadcast_evidence_list()

        self.broadcast_ooc(
            f'{client.char_name} [{client.id}] is CM in this area now.')

    def remove_owner(self, client):
        """
        Remove a CM from the area.
        """
        self._owners.remove(client)

        # Make sure the client's available areas are updated
        self.broadcast_area_list(client)

        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA
        # This should be remade by only sending updates to those players
        # who would actually be affected, and all players who don't need
        # an update are ignored.
        self.area_manager.send_arup_players()
        self.area_manager.send_arup_status()
        self.area_manager.send_arup_cms()
        self.area_manager.send_arup_lock()
        # HAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHAHHAHAHAHAHA

        self.broadcast_evidence_list()

        self.broadcast_ooc(
            f'{client.char_name} [{client.id}] is no longer CM in this area.')

    def broadcast_area_list(self, client=None):
        """
        Send the accessible and visible areas to the client.
        """
        clients = []
        if client == None:
            clients = list(self.clients)
        else:
            clients.append(client)

        for c in clients:
            allowed = c in self.owners or c.is_mod
            c.reload_area_list(c.get_area_list(not allowed, not allowed))

    def time_until_move(self, client):
        """
        Sum up the movement delays. For example,
        if client has 1s move delay, area has 3s move delay, and hub has 2s move delay,
        the resulting delay will be 1+3+2=6 seconds.
        Negative numbers are allowed.
        :return: time left until you can move again or 0.
        """
        secs = round(time.time() * 1000.0 - client.last_move_time)
        total = sum([client.move_delay, self.move_delay, self.area_manager.move_delay]) 
        test = total * 1000.0 - secs
        if test > 0:
            return test
        return 0

    class JukeboxVote:
        """Represents a single vote cast for the jukebox."""
        def __init__(self, client, name, length, showname):
            self.client = client
            self.name = name
            self.length = length
            self.chance = 1
            self.showname = showname
