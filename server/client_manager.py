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

import re
import string
import time
from heapq import heappop, heappush

from server import database
from server.constants import TargetType
from server.exceptions import ClientError, AreaError


class ClientManager:
    """Holds the list of all clients currently connected to the server."""
    class Client:
        """Represents a single instance of a user.

        Clients may only belong to a single room.
        """
        def __init__(self, server, transport, user_id, ipid):
            self.is_checked = False
            self.transport = transport
            self.hdid = ''
            self.id = user_id
            self.char_id = -1
            self.area = server.area_manager.default_area()
            self.server = server
            self.name = ''
            self.fake_name = ''
            self.is_mod = False
            self.mod_profile_name = None
            self.is_dj = True
            self.can_wtce = True
            self.pos = ''
            self.evi_list = []
            self.disemvowel = False
            self.shaken = False
            self.charcurse = []
            self.muted_global = False
            self.muted_adverts = False
            self.is_muted = False
            self.is_ooc_muted = False
            self.pm_mute = False
            self.mod_call_time = 0
            self.ipid = ipid

            # Pairing stuff
            self.charid_pair = -1
            self.offset_pair = 0
            self.last_sprite = ''
            self.flip = 0
            self.claimed_folder = ''

            # Casing stuff
            self.casing_cm = False
            self.casing_cases = ''
            self.casing_def = False
            self.casing_pro = False
            self.casing_jud = False
            self.casing_jur = False
            self.casing_steno = False
            self.case_call_time = 0

            # flood-guard stuff
            self.mus_counter = 0
            self.mus_mute_time = 0
            self.mus_change_time = [
                x * self.server.config['music_change_floodguard']
                ['interval_length']
                for x in range(self.server.config['music_change_floodguard']
                               ['times_per_interval'])
            ]
            self.wtce_counter = 0
            self.wtce_mute_time = 0
            self.wtce_time = [
                x * self.server.config['wtce_floodguard']['interval_length']
                for x in range(self.server.config['wtce_floodguard']
                               ['times_per_interval'])
            ]
            # security stuff
            self.clientscon = 0
            self.gm_save_time = 0

            # movement system stuff
            self.last_move_time = 0
            self.move_delay = 0

        def send_raw_message(self, msg):
            """
            Send a raw packet over TCP.
            :param msg: string to send
            """
            self.transport.write(msg.encode('utf-8'))

        def send_command(self, command, *args):
            """
            Compose and send an AO-compatible message, with arguments
            delimited by `#` and ending with `#%`.
            :param command: command name
            :param *args: list of arguments
            """
            if args:
                if command == 'MS':
                    for evi_num in range(len(self.evi_list)):
                        if self.evi_list[evi_num] == args[11]:
                            lst = list(args)
                            lst[11] = evi_num
                            args = tuple(lst)
                            break
                self.send_raw_message(
                    f'{command}#{"#".join([str(x) for x in args])}#%')
            else:
                self.send_raw_message(f'{command}#%')

        def send_ooc(self, msg):
            """
            Send an out-of-character message to the client.
            :param msg: message to send
            """
            self.send_command('CT', self.server.config['hostname'], msg, '1')

        def send_motd(self):
            """Send the message of the day to the client."""
            motd = self.server.config['motd']
            self.send_ooc(f'=== MOTD ===\r\n{motd}\r\n=============')

        def send_player_count(self):
            """
            Send a message stating the number of players currently online
            to the client.
            """
            players = self.server.player_count
            limit = self.server.config['playerlimit']
            self.send_ooc(f'{players}/{limit} players online.')

        def is_valid_name(self, name):
            """
            Check if the given string is valid as an OOC name.
            :param name: name to check
            """
            printset = set(string.ascii_letters + string.digits + "~ -_.',")
            name_ws = name.replace(' ', '')
            if not name_ws or name_ws.isdigit():
                return False
            if not set(name_ws).issubset(printset): #illegal chars in ooc name
                return False
            for client in self.server.client_manager.clients:
                if client.name == name:
                    return False
            return True

        def disconnect(self):
            """Disconnect the client gracefully."""
            self.transport.close()

        def change_character(self, char_id, force=False):
            """
            Change the client's character or force the character selection
            screen to appear for the client.
            :param char_id: character ID to switch to
            :param force: whether or not the client is forced to switch
            to another character if the target character is not available
            (Default value = False)
            """
            if not self.server.is_valid_char_id(char_id):
                raise ClientError('Invalid character ID.')
            if len(self.charcurse) > 0:
                if not char_id in self.charcurse:
                    raise ClientError('Character not available.')
                force = True
            if not self.area.is_char_available(char_id):
                if force:
                    for client in self.area.clients:
                        if client.char_id == char_id:
                            client.char_select()
                else:
                    raise ClientError('Character not available.')
            old_char = self.char_name
            self.char_id = char_id
            self.pos = ''
            self.send_command('PV', self.id, 'CID', self.char_id)
            self.area.send_command('CharsCheck',
                                   *self.get_available_char_list())

            new_char = self.char_name
            database.log_room('char.change', self, self.area,
                message={'from': old_char, 'to': new_char})

        def change_music_cd(self):
            """
            Check if the client can change music or not.
            :returns: how many seconds the client must wait to change music
            """
            if self.is_mod or self in self.area.owners:
                return 0
            if self.mus_mute_time:
                if time.time() - self.mus_mute_time < self.server.config[
                        'music_change_floodguard']['mute_length']:
                    return self.server.config['music_change_floodguard'][
                        'mute_length'] - (time.time() - self.mus_mute_time)
                else:
                    self.mus_mute_time = 0
            times_per_interval = self.server.config['music_change_floodguard'][
                'times_per_interval']
            interval_length = self.server.config['music_change_floodguard'][
                'interval_length']
            if time.time() - self.mus_change_time[
                (self.mus_counter - times_per_interval + 1) %
                    times_per_interval] < interval_length:
                self.mus_mute_time = time.time()
                return self.server.config['music_change_floodguard'][
                    'mute_length']
            self.mus_counter = (self.mus_counter + 1) % times_per_interval
            self.mus_change_time[self.mus_counter] = time.time()
            return 0

        def wtce_mute(self):
            """
            Check if the client can use WT/CE or not.
            :returns: how many seconds the client must wait to use WT/CE
            """
            if self.is_mod or self in self.area.owners:
                return 0
            if self.wtce_mute_time:
                if time.time() - self.wtce_mute_time < self.server.config[
                        'wtce_floodguard']['mute_length']:
                    return self.server.config['wtce_floodguard'][
                        'mute_length'] - (time.time() - self.wtce_mute_time)
                else:
                    self.wtce_mute_time = 0
            times_per_interval = self.server.config['wtce_floodguard'][
                'times_per_interval']
            interval_length = self.server.config['wtce_floodguard'][
                'interval_length']
            if time.time() - self.wtce_time[
                (self.wtce_counter - times_per_interval + 1) %
                    times_per_interval] < interval_length:
                self.wtce_mute_time = time.time()
                return self.server.config['music_change_floodguard'][
                    'mute_length']
            self.wtce_counter = (self.wtce_counter + 1) % times_per_interval
            self.wtce_time[self.wtce_counter] = time.time()
            return 0

        def reload_character(self):
            """Reload the state of the current character."""
            try:
                self.change_character(self.char_id, True)
            except ClientError:
                raise

        def reload_music_list(self, music=[]):
            """
            Rebuild the music list with the provided array, or the server music list as a whole.
            """
            song_list = []

            if (len(music) > 0):
                song_list = music
            else:
                song_list = self.server.music_list

            song_list = self.server.build_music_list_ao2(song_list)
            # KEEP THE ASTERISK
            self.send_command('FM', *song_list)

        def reload_area_list(self, areas=[]):
            """
            Rebuild the area list according to provided areas list.
            """
            area_list = []

            if (len(areas) > 0):
                area_list = areas

            # KEEP THE ASTERISK
            self.send_command('FA', *area_list)


        def change_area(self, area):
            """
            Switch the client to another area, unless the area is locked.
            :param area: area to switch to
            """
            if self.area == area:
                raise ClientError('User already in specified area.')
            if area.is_locked == area.Locked.LOCKED and not self.is_mod and not self.id in area.invite_list:
                raise ClientError('That area is locked!')
            if area.is_locked == area.Locked.SPECTATABLE and not self.is_mod and not self.id in area.invite_list:
                self.send_ooc(
                    'This area is spectatable, but not free - you cannot talk in-character unless invited.'
                )

            if self in self.area.afkers:
                self.server.client_manager.toggle_afk(self)
            if self.area.jukebox:
                self.area.remove_jukebox_vote(self, True)

            old_area = self.area
            if not area.is_char_available(self.char_id):
                try:
                    new_char_id = area.get_rand_avail_char_id()
                except AreaError:
                    raise ClientError('No available characters in that area.')

                self.change_character(new_char_id)
                self.send_ooc(
                    f'Character taken, switched to {self.char_name}.')

            self.area.remove_client(self)
            self.area = area
            area.new_client(self)

            self.send_ooc(
                f'Changed area to {area.name} [{self.area.status}].')
            self.area.send_command('CharsCheck',
                                   *self.get_available_char_list())
            self.area.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background, self.pos)
            self.send_command('LE', *self.area.get_evidence_list(self))

        def send_area_list(self):
            """Send a list of areas over OOC."""
            msg = '=== Areas ==='
            for _, area in enumerate(self.server.area_manager.areas):
                owner = 'FREE'
                if len(area.owners) > 0:
                    owner = f'CMs: {area.get_cms()}'
                lock = {
                    area.Locked.FREE: '',
                    area.Locked.SPECTATABLE: '[SPECTATABLE]',
                    area.Locked.LOCKED: '[LOCKED]'
                }
                msg += f'\r\nArea {area.abbreviation}: {area.name} (users: {len(area.clients)}) [{area.status}][{owner}]{lock[area.is_locked]}'
                if self.area == area:
                    msg += ' [*]'
            self.send_ooc(msg)

        def get_area_info(self, area_id, mods, afk_check):
            """
            Get information about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            :param afk_check: Limit player list to afks
            :returns: information as a string
            """
            info = '\r\n'
            try:
                area = self.server.area_manager.get_area_by_id(area_id)
            except AreaError:
                raise
            info += f'=== {area.name} ==='
            info += '\r\n'

            lock = {
                area.Locked.FREE: '',
                area.Locked.SPECTATABLE: '[SPECTATABLE]',
                area.Locked.LOCKED: '[LOCKED]'
            }
            if afk_check:
                player_list = area.afkers
            else:
                player_list = area.clients
            info += f'[{area.abbreviation}]: [{len(player_list)} users][{area.status}]{lock[area.is_locked]}'

            sorted_clients = []
            for client in player_list:
                if (not mods) or client.is_mod:
                    sorted_clients.append(client)
            for owner in area.owners:
                if not (mods or owner in player_list):
                    sorted_clients.append(owner)
            if not sorted_clients:
                return ''
            sorted_clients = sorted(sorted_clients,
                                    key=lambda x: x.char_name or '')
            for c in sorted_clients:
                info += '\r\n'
                if c in area.owners:
                    if not c in player_list:
                        info += '[RCM]'
                    else:
                        info += '[CM]'
                if c in area.afkers:
                    info += '[AFK]'
                info += f' [{c.id}] {c.char_name}'
                if self.is_mod:
                    info += f' ({c.ipid}): {c.name}'
            return info

        def send_area_info(self, area_id, mods, afk_check=False):
            """
            Send information over OOC about a specific area.
            :param area_id: area ID
            :param mods: limit player list to mods
            :param afk_check: Limit player list to afks
            """
            # if area_id is -1 then return all areas. If mods is True then return only mods
            info = ''
            if area_id == -1:
                # all areas info
                cnt = 0
                info = '\n== Area List =='
                for i in range(len(self.server.area_manager.areas)):
                    client_list = self.server.area_manager.areas[i]
                    if afk_check:
                        client_list = client_list.afkers
                    else:
                        client_list = client_list.clients
                    area_info = self.get_area_info(i, mods, afk_check)
                    if len(client_list) > 0 or len(
                               self.server.area_manager.areas[i].owners) > 0:
                        cnt += len(client_list)
                        info += f'{area_info}'
                if afk_check:
                    info = f'Current AFK-ers: {cnt}{info}'
                else:
                    info = f'Current online: {cnt}{info}'
            else:
                try:
                    client_list = self.server.area_manager.areas[area_id]
                    if afk_check:
                        client_list = client_list.afkers
                    else:
                        client_list = client_list.clients
                    area_info = self.get_area_info(area_id, mods, afk_check)
                    area_client_cnt = len(client_list)
                    if afk_check:
                        info = f'People AFK-ing in this area: {area_client_cnt}'
                    else:
                        info = f'People in this area: {area_client_cnt}'
                    info += area_info

                except AreaError:
                    raise
            self.send_ooc(info)

        def send_done(self):
            """
            Send area information and finish the join handshake.
            This unconditionally causes the client to show the character
            selection screen, even if the client has already joined.
            """
            self.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background, self.pos)
            self.send_command('LE', *self.area.get_evidence_list(self))
            self.send_command('MM', 1)

            self.server.area_manager.send_arup_players()
            self.server.area_manager.send_arup_status()
            self.server.area_manager.send_arup_cms()
            self.server.area_manager.send_arup_lock()

            self.send_command('DONE')

        def char_select(self):
            """Force the client to select a different character."""
            self.char_id = -1
            self.send_done()

        def get_available_char_list(self):
            """Get a list of character IDs that the client can select."""
            if len(self.charcurse) > 0:
                avail_char_ids = set(range(len(
                    self.server.char_list))) and set(self.charcurse)
            else:
                avail_char_ids = set(range(len(self.server.char_list))) - {
                    x.char_id
                    for x in self.area.clients
                }
            char_list = [-1] * len(self.server.char_list)
            for x in avail_char_ids:
                char_list[x] = 0
            return char_list

        def auth_mod(self, password):
            """
            Attempt to log in as a moderator.
            :param password: password string
            :returns: name of profile which the password belongs to, if login
            was successful
            :raises: ClientError if password is incorrect
            """
            modpasses = self.server.config['modpass']
            if isinstance(modpasses, dict):
                matches = [k for k in modpasses
                    if modpasses[k]['password'] == password]
            elif modpasses == password:
                matches = ['default']
            else:
                matches = []

            if self.is_mod:
                raise ClientError('Already logged in.')
            elif len(matches) > 0:
                self.is_mod = True
                self.mod_profile_name = matches[0]
                return self.mod_profile_name
            else:
                raise ClientError('Invalid password.')

        @property
        def ip(self):
            """Get an anonymized version of the IP address."""
            return self.ipid

        @property
        def char_name(self):
            """Get the name of the character that the client is using."""
            if self.char_id == -1:
                return None
            return self.server.char_list[self.char_id]

        def change_position(self, pos=''):
            """
            Change the character's current position in the area.
            :param pos: position in area (Default value = '')
            """
            self.pos = pos
            self.send_ooc(f'Position set to {pos}.')
            self.send_command('SP', self.pos) #Send a "Set Position" packet
            self.area.update_evidence_list(self) #Receive evidence

        def set_mod_call_delay(self):
            """Begin the mod call cooldown."""
            self.mod_call_time = round(time.time() * 1000.0 + 30000)

        def can_call_mod(self):
            """Whether or not the client can currently call mod."""
            return (time.time() * 1000.0 - self.mod_call_time) > 0

        def set_case_call_delay(self):
            """Begin the case announcement cooldown."""
            self.case_call_time = round(time.time() * 1000.0 + 60000)

        def can_call_case(self):
            """Whether or not the client can currently announce a case."""
            return (time.time() * 1000.0 - self.case_call_time) > 0

        def disemvowel_message(self, message):
            """Disemvowel a chat message."""
            message = re.sub('[aeiou]', '', message, flags=re.IGNORECASE)
            return re.sub(r'\s+', ' ', message)

        def shake_message(self, message):
            """Mix the words in a chat message."""
            import random
            parts = message.split()
            random.shuffle(parts)
            return ' '.join(parts)

    def __init__(self, server):
        self.clients = set()
        self.server = server
        self.cur_id = [i for i in range(self.server.config['playerlimit'])]

    def new_client_preauth(self, client):
        maxclients = self.server.config['multiclient_limit']
        for c in self.server.client_manager.clients:
            if c.ipid == client.ipid:
                if c.clientscon > maxclients:
                    return False
        return True

    def new_client(self, transport):
        """
        Create a new client, add it to the list, and assign it a player ID.
        :param transport: asyncio transport
        """
        try:
            user_id = heappop(self.cur_id)
        except IndexError:
            transport.write(b'BD#This server is full.#%')
            raise ClientError

        peername = transport.get_extra_info('peername')[0]
        
        c = self.Client(
            self.server, transport, user_id,
            database.ipid(peername))
        self.clients.add(c)
        temp_ipid = c.ipid
        for client in self.server.client_manager.clients:
            if client.ipid == temp_ipid:
                client.clientscon += 1
        return c

    def remove_client(self, client):
        """
        Remove a disconnected client from the client list.
        :param client: disconnected client
        """
        if client.area.jukebox:
            client.area.remove_jukebox_vote(client, True)
        for a in self.server.area_manager.areas:
            if client in a.owners:
                a.owners.remove(client)
                client.server.area_manager.send_arup_cms()
                if len(a.owners) == 0:
                    if a.is_locked != a.Locked.FREE:
                        a.unlock()
        heappush(self.cur_id, client.id)
        temp_ipid = client.ipid
        for c in self.server.client_manager.clients:
            if c.ipid == temp_ipid:
                c.clientscon -= 1
        self.clients.remove(client)

    def get_targets(self, client, key, value, local=False, single=False):
        """
        Find players by a combination of identifying data.
        Possible keys: player ID, OOC name, character name, HDID, IPID,
        IP address (same as IPID)

        :param client: client
        :param key: the type of identifier that `value` represents
        :param value: data identifying a client
        :param local: search in current area only (Default value = False)
        :param single: search only a single user (Default value = False)
        """
        areas = None
        if local:
            areas = [client.area]
        else:
            areas = client.server.area_manager.areas
        targets = []
        if key == TargetType.ALL:
            for nkey in range(6):
                targets += self.get_targets(client, nkey, value, local)
        for area in areas:
            for client in area.clients:
                if key == TargetType.IP:
                    if value.lower().startswith(client.ip.lower()):
                        targets.append(client)
                elif key == TargetType.OOC_NAME:
                    if value.lower().startswith(
                            client.name.lower()) and client.name:
                        targets.append(client)
                elif key == TargetType.CHAR_NAME:
                    if value.lower().startswith(
                            client.char_name.lower()):
                        targets.append(client)
                elif key == TargetType.ID:
                    if client.id == value:
                        targets.append(client)
                elif key == TargetType.IPID:
                    if client.ipid == value:
                        targets.append(client)
                elif key == TargetType.AFK:
                    if client in area.afkers:
                        targets.append(client)
        return targets

    def get_muted_clients(self):
        """Get a list of muted clients."""
        clients = []
        for client in self.clients:
            if client.is_muted:
                clients.append(client)
        return clients

    def get_ooc_muted_clients(self):
        """Get a list of OOC-muted clients."""
        clients = []
        for client in self.clients:
            if client.is_ooc_muted:
                clients.append(client)
        return clients

    def toggle_afk(self, client):
            if client in client.area.afkers:
                client.area.broadcast_ooc('{} is no longer AFK.'.format(client.char_name))
                client.send_ooc('You are no longer AFK. Welcome back!')  # Making the server a bit friendly wouldn't hurt, right?
                client.area.afkers.remove(client)
            else:
                client.area.broadcast_ooc('{} is now AFK.'.format(client.char_name))
                client.send_ooc('You are now AFK. Have a good day!')
                client.area.afkers.append(client)
