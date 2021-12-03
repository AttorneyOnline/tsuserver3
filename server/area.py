# KFO-Server, an Attorney Online server
#
# Copyright (C) 2020 Crystalwarrior <varsash@gmail.com>
#
# Derivative of tsuserver3, an Attorney Online server. Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
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
import arrow
from enum import Enum

import oyaml as yaml #ordered yaml
import os
import datetime
import logging
logger = logging.getLogger('events')

from server import database
from server import commands
from server.evidence import EvidenceList
from server.exceptions import ClientError, AreaError, ArgumentError, ServerError
from server.constants import MusicEffect

from collections import OrderedDict

class Area:
    class Timer:
        """Represents a single instance of a timer in the area."""
        def __init__(self, _id, Set = False, started = False, static = None, target = None, area = None, caller = None):
            self.id = _id
            self.set = Set
            self.started = started
            self.static = static
            self.target = target
            self.area = area
            self.caller = caller
            self.schedule = None
            self.commands = []
        
        def timer_expired(self):
            if self.schedule:
                self.schedule.cancel()
            # Either the area or the hub was destroyed at some point
            if self.area == None or self == None:
                return
            self.area.broadcast_ooc(f'Timer {self.id+1} has expired.')
            self.call_commands()
            self.commands.clear()
            self.static = datetime.timedelta(0)
            self.started = False

        def call_commands(self):
            if self.caller == None:
                return
            if self.area == None or self == None:
                return
            if self.caller not in self.area.owners:
                return
            server = self.caller.server
            for cmd in self.commands:
                args = cmd.split(' ')
                cmd = args.pop(0).lower()
                arg = ''
                if len(args) > 0:
                    arg = ' '.join(args)[:1024]
                try:
                    called_function = f'ooc_cmd_{cmd}'
                    if len(server.command_aliases) > 0 and not hasattr(commands, called_function):
                        if cmd in server.command_aliases:
                            called_function = f'ooc_cmd_{server.command_aliases[cmd]}'
                    if not hasattr(commands, called_function):
                        self.caller.send_ooc(f'[Timer {self.id}] Invalid command: {cmd}. Use /help to find up-to-date commands.')
                        return
                    # Remember the old area.
                    old_area = self.caller.area
                    old_hub = self.caller.area.area_manager
                    self.caller.area = self.area
                    getattr(commands, called_function)(self.caller, arg)
                    if old_area and old_area in old_hub.areas:
                        self.caller.area = old_area
                    # else:
                    #     self.caller.set_area(old_hub.default_area())
                except (ClientError, AreaError, ArgumentError, ServerError) as ex:
                    self.caller.send_ooc(f'[Timer {self.id}] {ex}')
                except Exception as ex:
                    self.caller.send_ooc(f'[Timer {self.id}] An internal error occurred: {ex}. Please inform the staff of the server about the issue.')
                    logger.exception('Exception while running a command')

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
        self.locked = False
        self.muted = False
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
        self.client_music = True
        self.replace_music = False
        self.ambience = ''
        self.can_dj = True
        self.hidden = False
        self.can_whisper = True
        self.can_wtce = True
        self.music_autoplay = False
        self.can_change_status = True
        self.use_backgrounds_yaml = False
        self.can_spectate = True
        self.can_getarea = True
        self.can_cross_swords = False
        self.can_scrum_debate = False
        self.can_panic_talk_action = False
        self.force_sneak = False
        # Whether the area is dark or not
        self.dark = False
        # The background to set when area's lights are turned off
        self.background_dark = 'fxdarkness'
        # The pos to set when the area's lights are turned off
        self.pos_dark = 'wit'
        # The desc to set when the area's lights are turned off
        self.desc_dark = "It's pitch black in here, you can't see a thing!"
        # /prefs end

        # DR minigames
        # in seconds, 300s = 5m
        self.cross_swords_timer = 300
        # in seconds, 300s = 5m. How much time is added on top of cross swords.
        self.scrum_debate_added_time = 300
        # in seconds, 300s = 5m
        self.panic_talk_action_timer = 300
        # Cooldown in seconds, 300s = 5m
        self.minigame_cooldown = 300
        # Who's debating who
        self.red_team = set()
        self.blue_team = set()
        # Minigame name
        self.minigame = ''
        # Minigame schedule
        self.minigame_schedule = None
        # /end

        self.old_muted = False
        self.old_invite_list = set()

        # original states for resetting the area after all CMs leave in a single area CM hub
        self.o_name = self._name
        self.o_abbreviation = self.abbreviation
        self.o_doc = self.doc
        self.o_desc = self.desc
        self.o_background = self.background

        self.music_looper = None
        self.next_message_time = 0
        self.judgelog = []
        self.music = ''
        self.music_player = ''
        self.music_player_ipid = -1
        self.music_looping = 0
        self.music_effects = 0
        self.evi_list = EvidenceList()
        self.testimony = []
        self.testimony_title = ''
        self.testimony_index = -1
        self.recording = False
        self.last_ic_message = None
        self.cards = dict()
        self.votes = dict()
        self.password = ''

        self.jukebox_votes = []
        self.jukebox_prev_char_id = -1

        self.music_list = []

        self._owners = set()
        self.afkers = []

        # Dictionary of dictionaries with further info, examine def link for more info
        self.links = {}

        # Timers ID 1 thru 20, (indexes 0 to 19 in area), timer ID 0 is reserved for hubs.
        self.timers = [
            self.Timer(x) for x in range(20)
        ]

        self.demo = []
        self.demo_schedule = None

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
        self.o_name = self._name
        self.o_abbreviation = self.abbreviation
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

        if 'is_locked' in area:
            self.locked = False
            self.muted = False
            if area['is_locked'] == 'SPECTATABLE':
                self.muted = True
            elif area['is_locked'] == 'LOCKED':
                self.locked = True

        if 'background' in area:
            self.background = area['background']
            self.o_background = self.background
        if 'bg_lock' in area:
            self.bg_lock = area['bg_lock']
        if 'pos_lock' in area:
            _pos_lock = area['pos_lock'].split(' ')

        if len(_pos_lock) > 0:
            self.pos_lock.clear()
            for pos in _pos_lock:
                pos = pos.lower()
                if pos != "none" and not (pos in self.pos_lock):
                    self.pos_lock.append(pos.lower())

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
        if 'locked' in area:
            self.locked = area['locked']
        if 'muted' in area:
            self.muted = area['muted']
        if 'blankposting_allowed' in area:
            self.blankposting_allowed = area['blankposting_allowed']
        if 'hp_def' in area:
            self.hp_def = area['hp_def']
        if 'hp_pro' in area:
            self.hp_pro = area['hp_pro']
        if 'doc' in area:
            self.doc = area['doc']
            self.o_doc = self.doc
        if 'status' in area:
            self.status = area['status']
        if 'move_delay' in area:
            self.move_delay = area['move_delay']
        if 'hide_clients' in area:
            self.hide_clients = area['hide_clients']
        if 'music_autoplay' in area:
            self.music_autoplay = area['music_autoplay']
            if self.music_autoplay and 'music' in area:
                self.music = area['music']
                self.music_effects = area['music_effects']
                self.music_looping = area['music_looping']
        if 'max_players' in area:
            self.max_players = area['max_players']
        if 'desc' in area:
            self.desc = area['desc']
            self.o_desc = self.desc
        if 'music_ref' in area:
            self.music_ref = area['music_ref']
            if self.music_ref == '':
                self.clear_music()
        if self.music_ref != '':
            self.load_music(f'storage/musiclists/{self.music_ref}.yaml')
            
        if 'client_music' in area:
            self.client_music = area['client_music']
        if 'replace_music' in area:
            self.replace_music = area['replace_music']
        if 'ambience' in area:
            self.ambience = area['ambience']
        if 'can_dj' in area:
            self.can_dj = area['can_dj']
        if 'hidden' in area:
            self.hidden = area['hidden']
        if 'can_whisper' in area:
            self.can_whisper = area['can_whisper']
        if 'can_wtce' in area:
            self.can_wtce = area['can_wtce']
        if 'can_change_status' in area:
            self.can_change_status = area['can_change_status']
        if 'use_backgrounds_yaml' in area:
            self.use_backgrounds_yaml = area['use_backgrounds_yaml']
        if 'can_spectate' in area:
            self.can_spectate = area['can_spectate']
        if 'can_getarea' in area:
            self.can_getarea = area['can_getarea']
        if 'can_cross_swords' in area:
            self.can_cross_swords = area['can_cross_swords']
        if 'can_scrum_debate' in area:
            self.can_scrum_debate = area['can_scrum_debate']
        if 'can_panic_talk_action' in area:
            self.can_panic_talk_action = area['can_panic_talk_action']
        if 'force_sneak' in area:
            self.force_sneak = area['force_sneak']
        if 'password' in area:
            self.password = area['password']
        if 'dark' in area:
            self.dark = area['dark']
        if 'background_dark' in area:
            self.background_dark = area['background_dark']
        if 'pos_dark' in area:
            self.pos_dark = area['pos_dark']
        if 'desc_dark' in area:
            self.desc_dark = area['desc_dark']

        if 'evidence' in area and len(area['evidence']) > 0:
            self.evi_list.evidences.clear()
            self.evi_list.import_evidence(area['evidence'])
            self.broadcast_evidence_list()

        if 'links' in area and len(area['links']) > 0:
            self.links.clear()
            for key, value in area['links'].items():
                locked, hidden, target_pos, can_peek, evidence, password = False, False, '', True, [], ''
                if 'locked' in value:
                    locked = value['locked']
                if 'hidden' in value:
                    hidden = value['hidden']
                if 'target_pos' in value:
                    target_pos = value['target_pos']
                if 'can_peek' in value:
                    can_peek = value['can_peek']
                if 'evidence' in value:
                    evidence = value['evidence']
                if 'password' in value:
                    password = value['password']
                self.link(key, locked, hidden, target_pos, can_peek, evidence, password)

        # Update the clients in that area
        if self.dark:
            self.change_background(self.background_dark)
        else:
            self.change_background(self.background)
        self.change_hp(1, self.hp_def)
        self.change_hp(2, self.hp_pro)
        if self.ambience:
            self.set_ambience(self.ambience)
        if self.music_autoplay:
            for client in self.clients:
                client.send_command('MC', self.music, -1, '', self.music_looping, 0, self.music_effects)

    def save(self):
        area = OrderedDict()
        area['area'] = self.name
        area['background'] = self.background
        area['pos_lock'] = 'none'
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
        area['locked'] = self.locked
        area['muted'] = self.muted
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
        area['client_music'] = self.client_music
        if self.music_autoplay:
            area['music'] = self.music
            area['music_effects'] = self.music_effects
            area['music_looping'] = self.music_looping
        area['ambience'] = self.ambience
        area['can_dj'] = self.can_dj
        area['hidden'] = self.hidden
        area['can_whisper'] = self.can_whisper
        area['can_wtce'] = self.can_wtce
        area['can_change_status'] = self.can_change_status
        area['use_backgrounds_yaml'] = self.use_backgrounds_yaml
        area['can_spectate'] = self.can_spectate
        area['can_getarea'] = self.can_getarea
        area['can_cross_swords'] = self.can_cross_swords
        area['can_scrum_debate'] = self.can_scrum_debate
        area['can_panic_talk_action'] = self.can_panic_talk_action
        area['force_sneak'] = self.force_sneak
        area['password'] = self.password
        area['dark'] = self.dark
        area['background_dark'] = self.background_dark
        area['pos_dark'] = self.pos_dark
        area['desc_dark'] = self.desc_dark
        if len(self.evi_list.evidences) > 0:
            area['evidence'] = [e.to_dict() for e in self.evi_list.evidences]
        if len(self.links) > 0:
            area['links'] = self.links
        return area

    def new_client(self, client):
        """Add a client to the area."""
        self.clients.add(client)
        database.log_area('area.join', client, self)

        if self.music_autoplay:
            client.send_command('MC', self.music, -1, '', self.music_looping, 0, self.music_effects)

        # Update the timers
        timer = client.area.area_manager.timer
        if timer.set:
            s = int(not timer.started)
            current_time = timer.static
            if timer.started:
                current_time = timer.target - arrow.get()
            int_time = int(current_time.total_seconds()) * 1000
            # Unhide the timer
            client.send_command('TI', 0, 2, int_time)
            # Start the timer
            client.send_command('TI', 0, s, int_time)
        else:
            # Stop the timer
            client.send_command('TI', 0, 3, 0)
            # Hide the timer
            client.send_command('TI', 0, 1, 0)
        for timer_id, timer in enumerate(self.timers):
            # Send static time if applicable
            if timer.set:
                s = int(not timer.started)
                current_time = timer.static
                if timer.started:
                    current_time = timer.target - arrow.get()
                int_time = int(current_time.total_seconds()) * 1000
                # Start the timer
                client.send_command('TI', timer_id+1, s, int_time)
                # Unhide the timer
                client.send_command('TI', timer_id+1, 2, int_time)
                client.send_ooc(f'Timer {timer_id+1} is at {current_time}')
            else:
                # Stop the timer
                client.send_command('TI', timer_id+1, 1, 0)
                # Hide the timer
                client.send_command('TI', timer_id+1, 3, 0)

        # Play the ambience
        client.send_command('MC', self.ambience, -1, "", 1, 1, int(MusicEffect.FADE_OUT | MusicEffect.FADE_IN | MusicEffect.SYNC_POS))

    def remove_client(self, client):
        """Remove a disconnected client from the area."""
        if client.hidden_in != None:
            client.hide(False, hidden=True)
        if self.area_manager.single_cm:
            # Remove their owner status due to single_cm pref. remove_owner will unlock the area if they were the last CM.
            if client in self._owners:
                self.remove_owner(client)
                client.send_ooc('You can only be a CM of a single area in this hub.')
        if self.locking_allowed:
            # Since anyone can lock/unlock, unlock if we were the last client in this area and it was locked.
            if len(self.clients) - 1 <= 0:
                if self.locked:
                    self.unlock()
        self.clients.remove(client)
        if client in self.afkers:
            self.afkers.remove(client)
            self.server.client_manager.toggle_afk(client)
        if self.jukebox:
            self.remove_jukebox_vote(client, True)
        if len(self.clients) == 0:
            self.change_status('IDLE')
        database.log_area('area.leave', client, self)
        if not client.hidden:
            self.area_manager.send_arup_players()

        # Update everyone's available characters list
        # Commented out due to potentially causing clientside lag...
        # self.send_command('CharsCheck',
        #                     *client.get_available_char_list())

    def unlock(self):
        """Mark the area as unlocked."""
        self.locked = False
        self.area_manager.send_arup_lock()

    def lock(self):
        """Mark the area as locked."""
        self.locked = True
        self.area_manager.send_arup_lock()

    def mute(self):
        """Mute the area."""
        self.muted = True
        self.invite_list.clear()
        self.area_manager.send_arup_lock()

    def unmute(self):
        """Unmute the area."""
        self.muted = False
        self.invite_list.clear()
        self.area_manager.send_arup_lock()
    
    def link(self, target, locked=False, hidden=False, target_pos='', can_peek=True, evidence=[], password=''):
        """
        Sets up a one-way connection between this area and targeted area.
        Returns the link dictionary.
        :param target: the targeted Area ID to connect
        :param locked: is the link unusable?
        :param hidden: is the link invisible?
        :param target_pos: which position should we end up in when we come through
        :param can_peek: can you peek through this path?
        :param evidence: a list of evidence from which this link will be accessible when you hide in it

        """
        link = {
            "locked": locked,
            "hidden": hidden,
            "target_pos": target_pos,
            "can_peek": can_peek,
            "evidence": evidence,
            "password": password,
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
            if c in self.clients:
                continue
            if c.remote_listen == 3 or \
                    (cmd == 'CT' and c.remote_listen == 2) or \
                    (cmd == 'MS' and c.remote_listen == 1):
                c.send_command(cmd, *args)

    def send_owner_ic(self, bg, cmd, *args):
        """
        Send an IC message to all owners of the area
        that are not currently in the area, with the specified bg.
        """
        for c in self.owners:
            if c in self.clients:
                continue
            if c.remote_listen == 3 or \
                    (cmd == 'MS' and c.remote_listen == 1):
                if c.area.background != bg:
                    c.send_command('BN', bg)
                c.send_command(cmd, *args)
                if c.area.background != bg:
                    c.send_command('BN', c.area.background)

    def broadcast_ooc(self, msg):
        """
        Broadcast an OOC message to all clients in the area.
        :param msg: message
        """
        self.send_command('CT', self.server.config['hostname'], msg, '1')
        self.send_owner_command(
            'CT',
            f'[{self.id}]' + self.server.config['hostname'],
            msg, '1')
    
    def send_ic(self, client, *args, targets=None):
        """
        Send an IC message from a client to all applicable clients in the area.
        :param client: speaker
        :param *args: arguments
        """
        if client in self.afkers:
            client.server.client_manager.toggle_afk(client)
        if client and args[4].startswith('**') and len(self.testimony) > 0:
            idx = self.testimony_index
            if idx == -1:
                idx = 0
            try:
                lst = list(self.testimony[idx])
                lst[4] = "}}}" + args[4][2:]
                self.testimony[idx] = tuple(lst)
                self.broadcast_ooc(f'{client.showname} has amended Statement {idx+1}.')
                if not self.recording:
                    self.testimony_send(idx)
            except IndexError:
                client.send_ooc(f'Something went wrong, couldn\'t amend Statement {idx+1}!')
            return
        adding = args[4].strip() != '' and self.recording and client != None
        if client and args[4].startswith('++') and len(self.testimony) > 0:
            if len(self.testimony) >= 30:
                client.send_ooc('Maximum testimony statement amount reached! (30)')
                return
            adding = True
        else:
            if targets == None:
                targets = self.clients
            for c in targets:
                # Blinded clients don't receive IC messages
                if c.blinded:
                    continue
                # pos doesn't match listen_pos, we're not listening so make this an OOC message instead
                if c.listen_pos != None:
                    if type(c.listen_pos) is list and not (args[5] in c.listen_pos) or \
                        c.listen_pos == 'self' and args[5] != c.pos:
                        name = ''
                        if args[8] != -1:
                            name = self.server.char_list[args[8]]
                        if args[15] != '':
                            name = args[15]
                        # Send the mesage as OOC.
                        # Woulda been nice if there was a packet to send messages to IC log
                        # without displaying it in the viewport.
                        c.send_command('CT', f'[pos \'{args[5]}\'] {name}', args[4])
                        continue
                complete = args
                # First-person mode support, we see our own msgs as narration
                if c == client and client.firstperson:
                    lst = list(args)
                    lst[3] = '' # Change anim to '' which should start narrator mode
                    complete = tuple(lst)
                c.send_command('MS', *complete)

            # args[4] = msg
            # args[15] = showname
            name = ''
            if args[8] != -1:
                name = self.server.char_list[args[8]]
            if args[15] != '':
                name = args[15]

            delay = 200 + self.parse_msg_delay(args[4])
            self.next_message_time = round(time.time() * 1000.0 + delay)

            # Objection used
            if str(args[10]).split('<and>')[0] == '2':
                msg = args[4].lower()
                target = ''
                is_pta = False
                # contains word "pta" in message
                if ' pta' in f' {msg} ':
                    # formatting for `PTA @Jack` or `@Jack PTA`
                    is_pta = True
                # message contains an "at" sign aka we're referring to someone specific
                if '@' in msg:
                    # formatting for `PTA@Jack`
                    if msg.startswith('pta'):
                        is_pta = True
                    target = msg[msg.find('@')+1:]
                target = target.lower()
                if target != '':
                    try:
                        opponent = None
                        for t in self.clients:
                            # Ignore ourselves
                            if t == client:
                                continue
                            # We're @num so we're trying to grab a Client ID, don't do shownames
                            if target.strip().isnumeric():
                                if t.id == int(target):
                                    opponent = t
                                    break
                            # Loop through the shownames if it's @text
                            if target in t.showname.lower():
                                opponent = t

                        if opponent != None:
                            self.start_debate(client, opponent, is_pta)
                        else:
                            raise AreaError('Interjection minigame - target not found!')
                    except Exception as ex:
                        client.send_ooc(ex)
                        return

            if client:
                if args[4].strip() != '' or self.last_ic_message == None or args[8] != self.last_ic_message[8] or self.last_ic_message[4].strip() != '':
                    database.log_area('chat.ic', client, client.area, message=args[4])
                if self.recording:
                    # See if the testimony is supposed to end here.
                    scrunched = ''.join(e for e in args[4] if e.isalnum())
                    if len(scrunched) > 0 and scrunched.lower() == 'end':
                        self.recording = False
                        self.broadcast_ooc(f'[{client.id}] {client.showname} has ended the testimony.')
                        self.send_command('RT', 'testimony1', 1)
                        return
            self.last_ic_message = args

        if adding:
            if len(self.testimony) >= 30:
                client.send_ooc('Maximum testimony statement amount reached! (30)')
                return
            lst = list(args)
            if lst[4].startswith('++'):
                lst[4] = lst[4][2:]
            # Remove speed modifying chars and start the statement instantly
            lst[4] = "}}}" + lst[4].replace('{', '').replace('}', '')
            # Non-int pre automatically enabled
            lst[18] = 1
            # Set emote_mod to conform to nonint_pre
            if lst[7] == 1 or lst[7] == 2:
                lst[7] = 0
            elif lst[7] == 6:
                lst[7] = 5
            # Make it green
            lst[14] = 1
            rec = tuple(lst)
            idx = self.testimony_index
            if idx == -1:
                # Add one statement at the very end.
                self.testimony.append(rec)
                idx = self.testimony.index(rec)
            else:
                # Add one statement ahead of the one we're currently on.
                idx += 1
                self.testimony.insert(idx, rec)
            self.broadcast_ooc(f'Statement {idx+1} added.')
            if not self.recording:
                self.testimony_send(idx)
    
    def testimony_send(self, idx):
        """Send the testimony statement at index"""
        try:
            statement = self.testimony[idx]
            self.testimony_index = idx
            targets = self.clients
            for c in targets:
                # Blinded clients don't receive IC messages
                if c.blinded:
                    continue
                # Ignore those losers with listenpos for testimony
                c.send_command('MS', *statement)
        except (ValueError, IndexError):
            raise AreaError('Invalid testimony reference!')

    def parse_msg_delay(self, msg):
        """ Parses the correct delay for the message supporting escaped characters and }}} {{{ speed-ups/slowdowns.
        :param msg: the string
        :return: delay integer in ms
        """
        #Fastest - Default - Slowest. These are default values in ms for KFO Client.
        message_display_speed = [0, 10, 25, 40, 50, 70, 90]

        #Starts in the middle of the messageDisplaySpeed list
        current_display_speed = 3

        #The 'meh' part of this is we can't exactly calculate accurately if color chars are used (as they could change clientside).
        formatting_chars = "@$`|_~%\\}{" 

        calculated_delay = 0

        escaped = False

        for symbol in msg:
            if symbol in formatting_chars and not escaped:
                if symbol == "\\":
                    escaped = True
                elif symbol == "{": #slow down
                    current_display_speed = min(len(message_display_speed)-1, current_display_speed + 1)
                elif symbol == "}": #speed up
                    current_display_speed = max(0, current_display_speed - 1)
                continue
            elif escaped and symbol == "n": #Newline monstrosity
                continue
            calculated_delay += message_display_speed[current_display_speed]
        return calculated_delay

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
        if preanim.lower().startswith('base/') or anim.lower().startswith('base/') or char.lower().startswith('base/'):
            # Prohibit absolute base/ paths
            return True
        if char.lower() != client.char_name.lower():
            for char_link in self.server.allowed_iniswaps:
                # Only allow if both the original character and the
                # target character are in the allowed INI swap list
                if client.char_name in char_link and char in char_link:
                    return False
            return True
        return not self.server.char_emotes[char].validate(preanim, anim, "")# sfx)

    def clear_music(self):
        self.music_list.clear()
        self.music_ref = ''

    def load_music(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as stream:
                music_list = yaml.safe_load(stream)

            prepath = ''
            for item in music_list:
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
            self.music_list = music_list
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
        if client.change_music_cd():
            client.send_ooc(
                f'You changed the song too many times. Please try again after {int(client.change_music_cd())} seconds.'
            )
            return
        if length == 0:
            self.remove_jukebox_vote(client, False)
            if len(self.jukebox_votes) <= 1 or (not self.music_looper or self.music_looper.cancelled()):
                self.start_jukebox()
        else:
            self.remove_jukebox_vote(client, True)
            self.jukebox_votes.append(
                self.JukeboxVote(client, music_name, length, showname))
            client.send_ooc('Your song was added to the jukebox.')
            if len(self.jukebox_votes) == 1 or (not self.music_looper or self.music_looper.cancelled()):
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
            # Server music list
            song_list = self.server.music_list

            # Hub music list
            if self.area_manager.music_ref != '' and len(self.area_manager.music_list) > 0:
                if self.area_manager.replace_music:
                    song_list = self.area_manager.music_list
                else:
                    song_list = song_list + self.area_manager.music_list

            # Area music list
            if self.music_ref != '' and self.music_ref != self.area_manager.music_ref and len(self.music_list) > 0:
                if self.replace_music:
                    song_list = self.music_list
                else:
                    song_list = song_list + self.music_list

            songs = []
            for c in song_list:
                if 'category' in c:
                    # Either play a completely random category, or play a category the last song was in
                    if 'songs' in c:
                        if self.music == '' or self.music in [b['name'] for b in c['songs']]:
                            for s in c['songs']:
                                if s['length'] == 0 or s['name'] == self.music:
                                    continue
                                songs = songs + [s]
            song = random.choice(songs)
            return self.JukeboxVote(None, song['name'], song['length'], 'Jukebox')
        elif len(self.jukebox_votes) == 1:
            song = self.jukebox_votes[0]
            self.remove_jukebox_vote(song.client, True)
            return song
        else:
            weighted_votes = []
            for current_vote in self.jukebox_votes:
                i = 0
                while i < current_vote.chance:
                    weighted_votes.append(current_vote)
                    i += 1
            song = random.choice(weighted_votes)
            self.remove_jukebox_vote(song.client, True)
            return song

    def start_jukebox(self):
        """Initialize jukebox mode if needed and play the next track."""
        if self.music_looper:
            self.music_looper.cancel()

        # There is a probability that the jukebox feature has been turned off since then,
        # we should check that.
        # We also do a check if we were the last to play a song, just in case.
        if not self.jukebox:
            if self.music_player == 'The Jukebox' and self.music_player_ipid == 'has no IPID':
                self.music = ''
            return

        vote_picked = self.get_jukebox_picked()

        if vote_picked is None:
            self.music = ''
            self.send_command('MC', self.music, -1, '', 1, 0, int(MusicEffect.FADE_OUT))
            return
        
        if vote_picked.name == self.music:
            return

        if vote_picked.client != None:
            self.jukebox_prev_char_id = vote_picked.client.char_id
            if vote_picked.showname == '':
                self.send_command('MC', vote_picked.name,
                                    vote_picked.client.char_id, '', 1, 0, int(MusicEffect.FADE_OUT))
            else:
                self.send_command('MC', vote_picked.name,
                                    vote_picked.client.char_id,
                                    vote_picked.showname, 1, 0, int(MusicEffect.FADE_OUT))
        else:
            self.jukebox_prev_char_id = -1
            self.send_command('MC', vote_picked.name, 0, 'The Jukebox', 1, 0, int(MusicEffect.FADE_OUT))

        self.music_player = 'The Jukebox'
        self.music_player_ipid = 'has no IPID'
        self.music = vote_picked.name

        for current_vote in self.jukebox_votes:
            # Choosing the same song will get your votes down to 0, too.
            # Don't want the same song twice in a row!
            if current_vote.name == vote_picked.name:
                current_vote.chance = 0
            else:
                current_vote.chance += 1

        length = vote_picked.length - 3 # Remove a few seconds to have a smooth fade out
        if length <= 0: # Length not defined
            length = 120.0 # Play each song for at least 2 minutes

        self.music_looper = asyncio.get_event_loop().call_later(
            max(5, length), lambda: self.start_jukebox())

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
        self.music_looping = loop
        self.music_effects = effects
        self.send_command('MC', name, cid, showname, loop, 0, effects)

    def can_send_message(self, client):
        """
        Check if a client can send an IC message in this area.
        :param client: sender
        """
        return (time.time() * 1000.0 - self.next_message_time) > 0

    def cannot_ic_interact(self, client):
        """
        Check if this area is muted to a client.
        :param client: sender
        """
        return self.muted and not client.is_mod and not client in self.owners and not client.id in self.invite_list

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

    def change_background(self, bg, silent=False):
        """
        Set the background.
        :param bg: background name
        :raises: AreaError if `bg` is not in background list
        """
        if self.use_backgrounds_yaml:
            if len(self.server.backgrounds) <= 0:
                raise AreaError('backgrounds.yaml failed to initialize! Please set "use_backgrounds_yaml" to "false" in the config/config.yaml, or create a new "backgrounds.yaml" list in the "config/" folder.')
            if bg.lower() not in (name.lower() for name in self.server.backgrounds):
                raise AreaError(f'Invalid background name {bg}.\nPlease add it to the "backgrounds.yaml" or change the background name for area [{self.id}] {self.name}.')
        if self.dark:
            self.background_dark = bg
        else:
            self.background = bg
        for client in self.clients:
            #Update all clients to the pos lock
            if len(self.pos_lock) > 0 and client.pos not in self.pos_lock:
                client.change_position(self.pos_lock[0])
            if silent:
                client.send_command('BN', bg)
            else:
                client.send_command('BN', bg, client.pos)

    def change_status(self, value):
        """
        Set the status of the area.
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
            self.music_player = f'{showname} ({client.char_name})'
        else:
            self.music_player = client.char_name
        self.music_player_ipid = client.ipid
        self.music = name
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

    def get_owners(self):
        """
        Get a string of area's owners (CMs).
        :return: message
        """
        msg = ''
        for i in self._owners:
            msg += f'[{str(i.id)}] {i.showname}, '
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
        self.area_manager.send_arup_cms()
        self.broadcast_evidence_list()

        self.broadcast_ooc(
            f'{client.showname} [{client.id}] is CM in this area now.')

    def remove_owner(self, client, dc=False):
        """
        Remove a CM from the area.
        """
        self._owners.remove(client)
        if not dc and len(client.broadcast_list) > 0:
            client.broadcast_list.clear()
            client.send_ooc('Your broadcast list has been cleared.')

        if self.area_manager.single_cm and len(self._owners) == 0:
            if self.locked:
                self.unlock()
            if self.password != '':
                self.password = ''
            if self.muted:
                self.unmute()
                self.broadcast_ooc('This area is no longer muted.')
            self.name = self.o_name
            self.doc = self.o_doc
            self.desc = self.o_desc
            self.change_background(self.o_background)
            self.pos_lock.clear()

        if not dc:
            # Make sure the client's available areas are updated
            self.broadcast_area_list(client)
            self.area_manager.send_arup_cms()
            self.broadcast_evidence_list()

        self.broadcast_ooc(
            f'{client.showname} [{client.id}] is no longer CM in this area.')

    def broadcast_area_list(self, client=None, refresh=False):
        """
        Send the accessible and visible areas to the client.
        """
        clients = []
        if client == None:
            clients = list(self.clients)
        else:
            clients.append(client)

        update_clients = []
        for c in clients:
            allowed = c.is_mod or c in self.owners
            area_list = c.get_area_list(allowed, allowed)
            if refresh or c.local_area_list != area_list:
                update_clients.append(c)
                c.reload_area_list(area_list)

        # Update ARUP information only for those that need it
        if len(update_clients) > 0:
            self.area_manager.send_arup_status(update_clients)
            self.area_manager.send_arup_lock(update_clients)
            self.area_manager.send_arup_cms(update_clients)

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

    @property
    def minigame_time_left(self):
        """Time left on the currently running minigame."""
        if not self.minigame_schedule or self.minigame_schedule.cancelled():
            return 0
        return self.minigame_schedule.when() - asyncio.get_event_loop().time()

    def end_minigame(self, reason=''):
        if self.minigame_schedule:
            self.minigame_schedule.cancel()

        self.muted = self.old_muted
        self.invite_list = self.old_invite_list
        self.red_team.clear()
        self.blue_team.clear()
        # Timer ID 3 is reserved for minigames
        # 3 stands for unset and hide
        self.send_command('TI', 3, 3)
        self.send_ic(None, '1', 0, "", "../misc/blank", f"~~}}}}`{self.minigame} END!`\\n{reason}", "", "", 0, -1, 0, 0, [0], 0, 0, 0, "System", -1, "", "", 0, 0, 0, 0, "0", 0, "", "", "", 0, "")
        self.minigame = ''

    def start_debate(self, client, target, pta=False):
        if (client.char_id in self.red_team and target.char_id in self.blue_team) or (client.char_id in self.blue_team and target.char_id in self.red_team):
            raise AreaError("Target is already on the opposing team!")

        if self.minigame == 'Scrum Debate':
            if target.char_id in self.red_team:
                self.red_team.discard(client.char_id)
                self.blue_team.add(client.char_id)
                self.invite_list.add(client.id)
                team = '🔵blue'
            elif target.char_id in self.blue_team:
                self.blue_team.discard(client.char_id)
                self.red_team.add(client.char_id)
                self.invite_list.add(client.id)
                team = '🔴red'
            else:
                raise AreaError('Target is not part of the minigame!')

            if len(self.blue_team) <= 0:
                self.broadcast_ooc('🔵Blue team conceded!')
                self.end_minigame('√Blue√ team conceded!')
                return
            elif len(self.red_team) <= 0:
                self.broadcast_ooc('🔴Red team conceded!')
                self.end_minigame('~Red~ team conceded!')
                return
            self.broadcast_ooc(f'[{client.id}] {client.showname} is now part of the {team} team!')
            database.log_area('minigame.sd', client, client.area, target=target, message=f'{self.minigame} is now part of the {team} team!')
            return
        elif self.minigame == 'Cross Swords':
            if target == client:
                self.broadcast_ooc(f'[{client.id}] {client.showname} conceded!')
                self.end_minigame(f'[{client.id}] {client.showname} conceded!')
                return
            if not self.can_scrum_debate:
                raise AreaError('You may not scrum debate in this area!')
            if target.char_id in self.red_team:
                self.red_team.discard(client.char_id)
                self.blue_team.add(client.char_id)
                self.invite_list.add(client.id)
                team = '🔵blue'
            elif target.char_id in self.blue_team:
                self.blue_team.discard(client.char_id)
                self.red_team.add(client.char_id)
                self.invite_list.add(client.id)
                team = '🔴red'
            else:
                raise AreaError('Target is not part of the minigame!')
            timeleft = self.minigame_schedule.when() - asyncio.get_event_loop().time()
            self.minigame_schedule.cancel()
            self.minigame = 'Scrum Debate'
            timer = timeleft + self.scrum_debate_added_time
            self.broadcast_ooc(f'[{client.id}] {client.showname} is now part of the {team} team!')
            database.log_area('minigame.sd', client, client.area, target=target, message=f'{self.minigame} is now part of the {team} team!')
        elif self.minigame == '':
            if not pta and not self.can_cross_swords:
                raise AreaError('You may not Cross-Swords in this area!')
            if pta and not self.can_panic_talk_action:
                raise AreaError('You may not PTA in this area!')
            if client == target:
                raise AreaError('You cannot initiate a minigame against yourself!')
            self.old_invite_list = self.invite_list
            self.old_muted = self.muted

            self.muted = True
            self.invite_list.clear()
            self.invite_list.add(client.id)
            self.invite_list.add(target.id)

            self.red_team.clear()
            self.blue_team.clear()
            self.red_team.add(client.char_id)
            self.blue_team.add(target.char_id)
            if pta:
                self.minigame = 'Panic Talk Action'
                timer = self.panic_talk_action_timer
                database.log_area('minigame.pta', client, client.area, target=target, message=f'{self.minigame} {client.showname} VS {target.showname}')
            else:
                self.minigame = 'Cross Swords'
                timer = self.cross_swords_timer
                database.log_area('minigame.cs', client, client.area, target=target, message=f'{self.minigame} {client.showname} VS {target.showname}')
        else:
            if target == client:
                self.broadcast_ooc(f'[{client.id}] {client.showname} conceded!')
                self.end_minigame(f'[{client.id}] {client.showname} conceded!')
                return
            raise AreaError(f'{self.minigame} is happening! You cannot interrupt it.')

        timer = max(5, int(timer))
        # Timer ID 3 is reserved for minigames
        # 1 afterwards is to start timer
        print('TI', 3, 0, timer * 1000)
        self.send_command('TI', 3, 2)
        self.send_command('TI', 3, 0, timer * 1000)
        self.minigame_schedule = asyncio.get_event_loop().call_later(
            timer, lambda: self.end_minigame('Timer expired!'))

        us = f'🔴[{client.id}] {client.showname} (Red)'
        them = f'🔵[{target.id}] {target.showname} (Blue)'
        for cid in self.blue_team:
            if client.char_id == cid:
                us = f'🔵[{client.id}] {client.showname} (Blue)'
                them = f'🔴[{target.id}] {target.showname} (Red)'
                break
        self.broadcast_ooc(f'❗{self.minigame}❗\n{us} objects to {them}!\n⏲You have {timer} seconds.\n/cs <id> to join the debate against target ID.')

    def play_demo(self, client):
        if self.demo_schedule:
            self.demo_schedule.cancel()
        if len(self.demo) <= 0:
            self.stop_demo()
            return

        packet = self.demo.pop(0)
        header = packet[0]
        args = packet[1:]
        if header.startswith('/'): # It's a command call
            # TODO: make this into a global function so commands can be called from anywhere in code...
            cmd = header[1:].lower()
            arg = ''
            if len(args) > 0:
                arg = ' '.join(args)[:1024]
            try:
                called_function = f'ooc_cmd_{cmd}'
                if len(client.server.command_aliases) > 0 and not hasattr(commands, called_function):
                    if cmd in client.server.command_aliases:
                        called_function = f'ooc_cmd_{client.server.command_aliases[cmd]}'
                if not hasattr(commands, called_function):
                    client.send_ooc(f'[Demo] Invalid command: {cmd}. Use /help to find up-to-date commands.')
                    self.stop_demo()
                    return
                getattr(commands, called_function)(client, arg)
            except (ClientError, AreaError, ArgumentError, ServerError) as ex:
                client.send_ooc(f'[Demo] {ex}')
                self.stop_demo()
                return
            except Exception as ex:
                client.send_ooc(f'[Demo] An internal error occurred: {ex}. Please inform the staff of the server about the issue.')
                logger.exception('Exception while running a command')
                self.stop_demo()
                return
        elif header == 'wait':
            secs = float(args[0]) / 1000
            self.demo_schedule = asyncio.get_event_loop().call_later(
                secs, lambda: self.play_demo(client))
            return
        elif len(client.broadcast_list) > 0:
            for area in client.broadcast_list:
                area.send_command(header, *args)
        else:
            self.send_command(header, *args)
        self.play_demo(client)

    def stop_demo(self):
        if self.demo_schedule:
            self.demo_schedule.cancel()
        self.demo.clear()

        # reset the packets the demo could have modified

        # Get defense HP bar
        self.send_command('HP', 1, self.hp_def)
        # Get prosecution HP bar
        self.send_command('HP', 2, self.hp_pro)

        # Send the background information
        if self.dark:
            self.send_command('BN', self.background_dark)
        else:
            self.send_command('BN', self.background)

    class JukeboxVote:
        """Represents a single vote cast for the jukebox."""
        def __init__(self, client, name, length, showname):
            self.client = client
            self.name = name
            self.length = length
            self.chance = 1
            self.showname = showname