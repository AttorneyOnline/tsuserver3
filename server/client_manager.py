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

from server import logger
from server.constants import TargetType
from server.exceptions import ClientError, AreaError


class ClientManager:
    class Client:
        def __init__(self, server, transport, user_id, ipid):
            self.is_checked = False
            self.transport = transport
            self.hdid = ''
            self.pm_mute = False
            self.id = user_id
            self.char_id = -1
            self.hub = server.hub_manager.default_hub()
            self.area = self.hub.default_area()
            self.server = server
            self.name = ''
            self.fake_name = ''
            self.is_mod = False
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
            self.command_time = 0
            self.in_rp = False
            self.ipid = ipid
            self.last_showname = ''

            #CMing stuff
            self.is_cm = False
            self.cm_log_type = ['MoveLog', 'ActionLog', 'PMLog', 'CharLog'] # If we're CM, we'll receive CM-related shenanigans
            self.broadcast_ic = []
            self.area_listen = []
            self.assigned_areas = [] #For /lock-ing and other fancy things as a normal player (still needs proximity w/ area access)
            self.hidden = False
            self.blinded = False
            self.blinded_by = None
            self.following = None
            self.sneak = False
            self.listenpos = False
            self.waiting_for_schedule = None
            self.ambience_editing = False

            # Pairing stuff
            self.charid_pair = -1
            self.offset_pair = 0
            self.last_sprite = ''
            self.flip = 0
            self.claimed_folder = ''

            # Casing stuff
            self.casing_cm = False
            self.casing_cases = ""
            self.casing_def = False
            self.casing_pro = False
            self.casing_jud = False
            self.casing_jur = False
            self.casing_steno = False
            self.case_call_time = 0

            # flood-guard stuff
            self.mus_counter = 0
            self.mus_mute_time = 0
            self.mus_change_time = [x * self.server.config['music_change_floodguard']['interval_length'] for x in
                                    range(self.server.config['music_change_floodguard']['times_per_interval'])]
            self.wtce_counter = 0
            self.wtce_mute_time = 0
            self.wtce_time = [x * self.server.config['wtce_floodguard']['interval_length'] for x in
                              range(self.server.config['wtce_floodguard']['times_per_interval'])]
            
            self.cm_save_time = 0

            self.last_move_time = 0
            self.move_delay = 0

        def send_raw_message(self, msg):
            self.transport.write(msg.encode('utf-8'))

        def send_command(self, command, *args):
            if args:
                if command == 'MS':
                    if self.blinded and args[0] != 'broadcast':
                        return #Don't receive any chat messages when blinded that are not broadcast_ic'ed
                    if self.listenpos and args[5] != self.pos: #pos doesn't match our current pos, we're not listening so make this an OOC message instead
                        name = self.server.char_list[args[8]]
                        if len(args[15]) > 0: #showname
                            name = args[15]
                        self.send_command('CT', f'<{args[5]}> {name}', args[4]) #send the mesage as OOC
                        return
                    if args[0] == 'broadcast':
                        lst = list(args)
                        lst[0] = '0'
                        args = tuple(lst)
                    for evi_num in range(len(self.evi_list)): #i sure would like to know what this does exactly
                        if self.evi_list[evi_num] == args[11]:
                            lst = list(args)
                            lst[11] = evi_num
                            args = tuple(lst)
                            break
                self.send_raw_message('{}#{}#%'.format(command, '#'.join([str(x) for x in args])))
            else:
                self.send_raw_message('{}#%'.format(command))

        def send_host_message(self, msg):
            self.send_command('CT', self.server.config['hostname'], msg, '1')

        def send_motd(self):
            self.send_host_message('=== MOTD ===\r\n{}\r\n============='.format(self.server.config['motd']))

        def send_player_count(self):
            self.send_host_message('{}/{} players online.'.format(
                self.server.get_player_count(),
                self.server.config['playerlimit']))

        def is_valid_name(self, name):
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
            self.transport.close()

        def change_character(self, char_id):
            if not self.server.is_valid_char_id(char_id):
                raise ClientError('Invalid Character ID.')
            allowed = self.is_cm or self.is_mod or self.get_char_name() == "Spectator" or self.server.char_list[char_id] == "Spectator"
            if len(self.charcurse) > 0:
                if not char_id in self.charcurse:
                    raise ClientError('Character not available.')
                # force = True
                allowed = True
            if not allowed and not self.area.is_char_available(char_id):
                # if force:
                #     for client in self.area.clients:
                #         if client.char_id == char_id:
                #             client.char_select()
                # else:
                raise ClientError('Character not available.')
            old_char = self.get_char_name()
            self.char_id = char_id
            self.pos = ''
            self.send_command('PV', self.id, 'CID', self.char_id)
            self.area.send_command('CharsCheck', *self.get_available_char_list())
            logger.log_server('Changed character from {} to {}.'.format(old_char, self.get_char_name()), self)
            self.hub.send_to_cm('CharLog', '[{}][{}]Changed character from {} to {}.'
                                .format(self.id, self.name, old_char, self.get_char_name()), self)

            if self.following != None:
                try:
                    c = self.server.client_manager.get_targets(
                        self, TargetType.ID, int(self.following), False)[0]
                    self.send_host_message(
                        'You are no longer following [{}] {}.'.format(c.id, c.get_char_name(True)))
                    self.following = None
                except:
                    self.following = None

        def change_music_cd(self):
            if self.is_mod or self.is_cm:
                return 0
            if self.mus_mute_time:
                if time.time() - self.mus_mute_time < self.server.config['music_change_floodguard']['mute_length']:
                    return self.server.config['music_change_floodguard']['mute_length'] - (
                            time.time() - self.mus_mute_time)
                else:
                    self.mute_time = 0
            times_per_interval = self.server.config['music_change_floodguard']['times_per_interval']
            interval_length = self.server.config['music_change_floodguard']['interval_length']
            if time.time() - self.mus_change_time[
                (self.mus_counter - times_per_interval + 1) % times_per_interval] < interval_length:
                self.mus_mute_time = time.time()
                return self.server.config['music_change_floodguard']['mute_length']
            self.mus_counter = (self.mus_counter + 1) % times_per_interval
            self.mus_change_time[self.mus_counter] = time.time()
            return 0
                
        def hide(self, tog=True):
            self.hidden = tog
            msg = 'no longer'
            if tog:
                msg = 'now'
            self.send_host_message('You are {} hidden from the area.'.format(msg))

        def blind(self, tog=True):
            self.blinded = tog
            msg = 'no longer'
            if tog:
                msg = 'now'
            self.send_host_message(
                'You are {} blinded from the area and seeing non-broadcasted IC messages.'.format(msg))
            self.area.update_evidence_list(self)

        def wtce_mute(self):
            if self.is_mod or self.is_cm:
                return 0
            if self.wtce_mute_time:
                if time.time() - self.wtce_mute_time < self.server.config['wtce_floodguard']['mute_length']:
                    return self.server.config['wtce_floodguard']['mute_length'] - (time.time() - self.wtce_mute_time)
                else:
                    self.wtce_mute_time = 0
            times_per_interval = self.server.config['wtce_floodguard']['times_per_interval']
            interval_length = self.server.config['wtce_floodguard']['interval_length']
            if time.time() - self.wtce_time[
                (self.wtce_counter - times_per_interval + 1) % times_per_interval] < interval_length:
                self.wtce_mute_time = time.time()
                return self.server.config['music_change_floodguard']['mute_length']
            self.wtce_counter = (self.wtce_counter + 1) % times_per_interval
            self.wtce_time[self.wtce_counter] = time.time()
            return 0

        def reload_character(self):
            try:
                self.change_character(self.char_id)
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

        def change_hub(self, hub):
            if self.hub == hub:
                raise ClientError('User already in specified hub.')
            self.hub = hub
            self.change_area(hub.default_area())

        def change_area(self, area, hidden=False):
            if self.area == area:
                raise ClientError('User already in specified area.')
            # if self.area.jukebox:
            #     self.area.remove_jukebox_vote(self, True)

            old_area = self.area
            allowed = self.is_cm or self.is_mod or self.get_char_name() == "Spectator"
            if not allowed and not area.is_char_available(self.char_id):
                try:
                    new_char_id = area.get_rand_avail_char_id()
                except AreaError:
                    raise ClientError('No available characters in that area.')

                self.change_character(new_char_id)
                self.send_host_message('Character taken, switched to {}.'.format(self.get_char_name()))

            self.area.remove_client(self)
            self.area = area
            if len(area.pos_lock) > 0:
                #We're going to change to the "default" poslock no matter what for the sake of puzzle rooms or the like having a "starting position".
                self.change_position(area.pos_lock[0])
            area.new_client(self)

            if old_area.hub != self.area.hub:
                old_area.hub.remove_client(self)
                self.area.hub.new_client(self)
            else:
                for c in area.hub.clients():
                    if c.following == self.id:
                        c.change_area(area)
                        c.send_host_message(
                            'Following [{}] {} to {}. [HUB: {}]'.format(self.id, self.get_char_name(True), area.name, area.hub.abbreviation))

            if not self.sneak and not hidden and not self.get_char_name() == "Spectator":
                old_area.send_host_message('[{}] {} leaves to [{}] {}. [HUB: {}]'.format(self.id, self.get_char_name(True), area.id, area.name, area.hub.abbreviation))
                area.send_host_message('[{}] {} enters from [{}] {}. [HUB: {}]'.format(self.id, self.get_char_name(True), old_area.id, old_area.name, old_area.hub.abbreviation))
            else:
                self.send_host_message('You moved to [{}] {} unannounced. [HUB: {}]'.format(area.id, area.name, area.hub.abbreviation))

            logger.log_server('Changed area from {} (A{} H{}) to {} (A{} H{}).'.format(old_area.name, old_area.id, old_area.hub.id, self.area.name, self.area.id, self.area.hub.id), self)
            self.area.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background, self.pos)
            if len(self.area.pos_lock) > 0:
                self.send_command('SD', '*'.join(self.area.pos_lock)) #set that juicy pos dropdown
            self.send_command('LE', *self.area.get_evidence_list(self))
            if self.area.desc != '':
                desc = self.area.desc[:128]
                if len(self.area.desc) > len(desc):
                    desc += "... Use /desc to read the rest."
                self.send_host_message('Area Description: {}'.format(desc))

        def get_area_list(self, hidden=False, accessible=False):
            area_list = []
            for area in self.hub.areas:
                if self.area != area and len(self.area.accessible) > 0 and not (area.id in self.area.accessible):
                    if accessible:
                        continue

                if hidden and self.area != area and area.is_hidden:
                    continue
                
                # if self.area == area:
                #     continue
                area_list.append(area)

            return area_list

        def show_area_list(self, hidden=False, accessible=False):
            acc = ''
            if accessible:
                acc = 'Accessible '
            msg = '=== {}Areas for Hub [{}]: {} ==='.format(acc, self.hub.id, self.hub.name)
            lock = {True: '[L]', False: ''}
            hide = {True: '[H]', False: ''}
            mute = {True: '[M]', False: ''}
            for area in self.get_area_list(hidden, accessible):
                users = ''
                lo = ''
                hi = ''
                acc = ''
                me = ''
                mu = ''
                if self.area != area and len(self.area.accessible) > 0 and not (area.id in self.area.accessible):
                    if not accessible:
                        acc = '<X>'

                if not hidden:
                    users = '(users: {}) '.format(len(area.clients))
                    lo = lock[area.is_locked]
                    hi = hide[area.is_hidden]
                    mu = mute[area.mute_ic]
                
                if self.area == area:
                    lo = lock[area.is_locked]
                    hi = hide[area.is_hidden]
                    mu = mute[area.mute_ic]
                    me = '[*]'

                msg += '\r\n{}Area {}: {}{} {}{}{}{}'.format(
                    me, area.id, acc, area.name, users, lo, hi, mu)
            self.send_host_message(msg)

        def send_hub_list(self):
            msg = '=== Hubs ==='.format(self.hub.name)
            for i, hub in enumerate(self.server.hub_manager.hubs):
                owner = 'FREE'
                if hub.master:
                    owner = 'MASTER: {}'.format(hub.master.name)
                msg += '\r\nHub {}: {} (users: {}) [{}][{}]'.format(
                    i, hub.name, len(hub.clients()), hub.status, owner)
                if self.hub == hub:
                    msg += ' [*]'
            self.send_host_message(msg)

        def get_area_info(self, area_id):
            try:
                area = self.hub.get_area_by_id(area_id)
            except AreaError:
                raise
            info = '= Area {}: {} =='.format(area.id, area.name)
            
            sorted_clients = []
            for client in area.clients:
                if (not client.hidden and client.get_char_name() != "Spectator") or self.is_cm or self.is_mod or self.get_char_name() == "Spectator":
                    sorted_clients.append(client)
            sorted_clients = sorted(sorted_clients, key=lambda x: x.get_char_name(True))
            for c in sorted_clients:
                info += '\r\n'
                if c == self:
                    info += '[*]'
                if c.is_cm:
                    info += '[CM]'
                if self.is_cm or self.is_mod:
                    info += '[{}] {}'.format(c.id, c.get_char_name(False))
                    if c.get_char_name() != c.get_char_name(True):
                        info += f' / {c.get_char_name(True)}'
                else:
                    info += '[{}] {}'.format(c.id, c.get_char_name(True))
                    if c.sneak: #alert the poor lad he got spotted
                        c.send_host_message(f'You\'ve been spotted by [{c.id}] {c.get_char_name(True)}!')
                if len(area.pos_lock) != 1 and c.pos != "": #we're not on a single-pos area
                    info += ' <{}>'.format(c.pos)
                if self.is_mod:
                    info += ' ({})'.format(c.ipid)
                if c.sneak:
                    info += ' [S]'
                if c.hidden:
                    info += ' [H]'
                if c.blinded:
                    info += ' [Z]' #for "catching some Z's"
            return info

        def send_area_info(self, area_id, hidden=False): 
            #if area_id is -1 then return all areas.
            info = ''
            if area_id == -1:
                # all areas info
                cnt = 0
                for i in range(len(self.hub.areas)):
                    if len(self.hub.areas[i].clients) > 0:
                        cnt += len(self.hub.areas[i].clients)
                        info += '\r\n{}'.format(self.get_area_info(i))
                if not hidden:
                    info = 'Current online: {}'.format(cnt) + info
            else:
                try:
                    info = ''
                    if not hidden:
                        info = 'People in this area: {}\n'.format(len(self.hub.clients()))
                    info += self.get_area_info(area_id)
                except AreaError:
                    raise
            self.send_host_message(info)

        def send_area_hdid(self, area_id):
            try:
                info = self.get_area_hdid(area_id)
            except AreaError:
                raise
            self.send_host_message(info)

        def send_all_area_hdid(self):
            info = '== HDID List =='
            for i in range (len(self.hub.areas)):
                 if len(self.hub.areas[i].clients) > 0:
                    info += '\r\n{}'.format(self.get_area_hdid(i))
            self.send_host_message(info)

        def send_all_area_ip(self):
            info = '== IP List =='
            for i in range (len(self.hub.areas)):
                 if len(self.hub.areas[i].clients) > 0:
                    info += '\r\n{}'.format(self.get_area_ip(i))
            self.send_host_message(info)

        def send_done(self):
            self.send_command('CharsCheck', *self.get_available_char_list())
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background, self.pos)
            if len(self.area.pos_lock) > 0:
                self.send_command('SD', '*'.join(self.area.pos_lock)) #set that juicy pos dropdown
            self.send_command('LE', *self.area.get_evidence_list(self))
            self.send_command('MM', 1)

            # self.server.hub_manager.send_arup_players()
            # self.server.hub_manager.send_arup_status()
            # self.server.hub_manager.send_arup_cms()
            # self.server.hub_manager.send_arup_lock()

            self.send_command('DONE')

        def char_select(self):
            self.char_id = -1
            self.send_done()

        def get_available_char_list(self):
            if len(self.charcurse) > 0:
                avail_char_ids = set(range(len(self.server.char_list))) and set(self.charcurse)
            else:
                avail_char_ids = set(range(len(self.server.char_list))) - set([x.char_id for x in self.area.clients])
            char_list = [-1] * len(self.server.char_list)
            for x in avail_char_ids:
                char_list[x] = 0
            return char_list

        def auth_mod(self, password):
            if self.is_mod:
                raise ClientError('Already logged in.')
            if password == self.server.config['modpass']:
                self.is_mod = True
            else:
                raise ClientError('Invalid password.')

        def get_ip(self):
            return self.ipid

        def get_char_name(self, custom=False):
            if self.char_id == -1:
                return 'CHAR_SELECT'
            if custom and self.last_showname != '':
                return self.last_showname
            return self.server.char_list[self.char_id]

        def change_position(self, pos=''):
            # if pos not in ('', 'def', 'pro', 'hld', 'hlp', 'jud', 'wit', 'jur', 'sea'):
            #     raise ClientError('Invalid position. Possible values: def, pro, hld, hlp, jud, wit, jur, sea.')
            self.pos = pos
            self.send_host_message('Position set to {}.'.format(pos))
            self.send_command('SP', self.pos) #Send a "Set Position" packet
            self.area.update_evidence_list(self) #Receive evidence

        def set_mod_call_delay(self):
            self.mod_call_time = round(time.time() * 1000.0 + 30000)

        def can_call_mod(self):
            return (time.time() * 1000.0 - self.mod_call_time) > 0

        def set_case_call_delay(self):
            self.case_call_time = round(time.time() * 1000.0 + 60000)

        def can_call_case(self):
            return (time.time() * 1000.0 - self.case_call_time) > 0

        def disemvowel_message(self, message):
            message = re.sub("[aeiou]", "", message, flags=re.IGNORECASE)
            return re.sub(r"\s+", " ", message)

        def shake_message(self, message):
            import random
            parts = message.split()
            random.shuffle(parts)
            return ' '.join(parts)

    def __init__(self, server):
        self.clients = set()
        self.server = server
        self.cur_id = [i for i in range(self.server.config['playerlimit'])]
        self.clients_list = []

    def new_client(self, transport):
        c = self.Client(self.server, transport, heappop(self.cur_id),
                        self.server.get_ipid(transport.get_extra_info('peername')[0]))
        self.clients.add(c)
        return c

    def remove_client(self, client):
        # if client.area.jukebox:
        #     client.area.remove_jukebox_vote(client, True)
        # for a in self.server.hub_manager.areas:
        #     if client in a.owners:
        #         a.owners.remove(client)
        #         client.server.hub_manager.send_arup_cms()
        #         if len(a.owners) == 0:
        #             if a.is_locked != a.Locked.FREE:
        #                 a.unlock()
        heappush(self.cur_id, client.id)
        self.clients.remove(client)

    def get_targets(self, client, key, value, local=False):
        # possible keys: ip, OOC, id, cname, ipid, hdid
        areas = None
        if local:
            areas = [client.area]
        else:
            areas = client.hub.areas
        targets = []
        if key == TargetType.ALL:
            for nkey in range(6):
                targets += self.get_targets(client, nkey, value, local)
        for area in areas:
            for client in area.clients:
                if key == TargetType.IP:
                    if value.lower().startswith(client.get_ip().lower()):
                        targets.append(client)
                elif key == TargetType.OOC_NAME:
                    if value.lower().startswith(client.name.lower()) and client.name:
                        targets.append(client)
                elif key == TargetType.CHAR_NAME:
                    if value.lower().startswith(client.get_char_name(True).lower()):
                        targets.append(client)
                elif key == TargetType.ID:
                    if client.id == value:
                        targets.append(client)
                elif key == TargetType.IPID:
                    if client.ipid == value:
                        targets.append(client)
        return targets

    def get_muted_clients(self):
        clients = []
        for client in self.clients:
            if client.is_muted:
                clients.append(client)
        return clients

    def get_ooc_muted_clients(self):
        clients = []
        for client in self.clients:
            if client.is_ooc_muted:
                clients.append(client)
        return clients
