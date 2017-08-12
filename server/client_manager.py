# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from server import fantacrypt
from server import logger
from server.exceptions import ClientError, AreaError

import time


class ClientManager:
    class Client:
        def __init__(self, server, transport, user_id, ipid):
            self.transport = transport
            self.hdid = ''
            self.pm_mute = False
            self.id = user_id
            self.char_id = -1
            self.area = server.area_manager.default_area()
            self.server = server
            self.name = ''
            self.is_mod = False
            self.pos = ''
            self.is_cm = False
            self.evi_list = []
            self.muted_global = False
            self.muted_adverts = False
            self.is_muted = False
            self.is_ooc_muted = False
            self.pm_mute = False
            self.mod_call_time = 0
            self.in_rp = False
            self.ipid = ipid

        def send_raw_message(self, msg):
            self.transport.write(msg.encode('utf-8'))

        def send_command(self, command, *args):
            if args:
                self.send_raw_message('{}#{}#%'.format(command, '#'.join([str(x) for x in args])))
            else:
                self.send_raw_message('{}#%'.format(command))

        def send_host_message(self, msg):
            self.send_command('CT', self.server.config['hostname'], msg)

        def send_motd(self):
            self.send_host_message('=== MOTD ===\r\n{}\r\n============='.format(self.server.config['motd']))

        def disconnect(self):
            self.transport.close()

        def change_character(self, char_id, force=False):
            if not self.server.is_valid_char_id(char_id):
                raise ClientError('Invalid Character ID.')
            if not force and not self.area.is_char_available(char_id):
                raise ClientError('Character not available.')
            elif not self.area.is_char_available(char_id):
                for client in self.area.clients:
                    if client.cid == char_id:
                        client.char_select()
            old_char = self.get_char_name()
            self.char_id = char_id
            self.send_command('PV', self.id, 'CID', self.char_id)
            logger.log_server('[{}]Changed character from {} to {}.'
                              .format(self.area.id, old_char, self.get_char_name()), self)

        def reload_character(self):
            try:
                self.change_character(self.char_id, True)
            except ClientError:
                raise

        def change_area(self, area):
            if self.area == area:
                raise ClientError('You are already in this area.')
            if area.is_locked and not self.is_mod:
                self.send_host_message("That area is locked!")
                return
            old_area = self.area
            if not area.is_char_available(self.char_id):
                try:
                    new_char_id = area.get_rand_avail_char_id()
                except AreaError:
                    raise ClientError('No available characters in that area.')

                self.change_character(new_char_id)
                self.send_host_message('Character taken, switched to {}.'.format(self.get_char_name()))

            self.area.remove_client(self)
            self.area = area
            area.new_client(self)

            self.send_host_message('Changed area to {}.[{}]'.format(area.name, self.area.status))
            logger.log_server(
                '[{}]Changed area from {} ({}) to {} ({}).'.format(self.get_char_name(), old_area.name, old_area.id,
                                                                   self.area.name, self.area.id), self)
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background)
            self.send_command('LE', *self.area.get_evidence_list(self))

        def send_area_list(self):
            msg = '=== Areas ==='
            for i, area in enumerate(self.server.area_manager.areas):
                msg += '\r\nArea {}: {} (users: {})'.format(i, area.name, len(area.clients))
                if self.area == area:
                    msg += ' [*]'
                msg += '\r\n[{}]'.format(area.status)
                if area.is_locked:
                    msg += '[LOCKED]'
            self.send_host_message(msg)

        def get_area_info(self, area_id, mods):
            info = ''
            try:
                area = self.server.area_manager.get_area_by_id(area_id)
            except AreaError:
                raise
            info += '= Area {}: {} =='.format(area.id, area.name)
            sorted_clients = []
            for client in area.clients:
                if (not mods) or client.is_mod:
                    sorted_clients.append(client)
            sorted_clients = sorted(sorted_clients, key=lambda x: x.get_char_name())
            for c in sorted_clients:
                info += '\r\n[{}] {}'.format(c.id, c.get_char_name())
                if self.is_mod:
                    info += ' ({})'.format(c.ipid)
            return info

        def send_area_info(self, area_id, mods): #if area_id is -1 then return all areas. If mods is True then return only mods
            info = ''
            if area_id == -1:
                # all areas info
                info = '== Area List =='
                for i in range(len(self.server.area_manager.areas)):
                    try:
                        if len(self.server.area_manager.areas[i].clients) > 0:
                            info += '\r\n{}'.format(self.get_area_info(i, mods))
                    except AreaError:
                        pass
            else:
                try:
                    info = self.get_area_info(area_id, mods)
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
            for i in range (len(self.server.area_manager.areas)):
                 if len(self.server.area_manager.areas[i].clients) > 0:
                    info += '\r\n{}'.format(self.get_area_hdid(i))
            self.send_host_message(info)

        def send_area_ip(self, area_id):
            try:
                info = self.get_area_ip(area_id)
            except AreaError:
                raise
            self.send_host_message(info)				

        def send_all_area_ip(self):
            info = '== IP List =='
            for i in range (len(self.server.area_manager.areas)):
                 if len(self.server.area_manager.areas[i].clients) > 0:
                    info += '\r\n{}'.format(self.get_area_ip(i))
            self.send_host_message(info)
			
        def send_done(self):
            avail_char_ids = set(range(len(self.server.char_list))) - set([x.char_id for x in self.area.clients])
            char_list = [-1] * len(self.server.char_list)
            for x in avail_char_ids:
                char_list[x] = 0
            self.send_command('CharsCheck', *char_list)
            self.send_command('HP', 1, self.area.hp_def)
            self.send_command('HP', 2, self.area.hp_pro)
            self.send_command('BN', self.area.background)
            self.send_command('LE', *self.area.get_evidence_list(self))
            self.send_command('MM', 1)
            self.send_command('OPPASS', fantacrypt.fanta_encrypt(self.server.config['guardpass']))
            self.send_command('DONE')

        def char_select(self):
            self.char_id = -1
            self.send_done()

        def auth_mod(self, password):
            if self.is_mod:
                raise ClientError('Already logged in.')
            if password == self.server.config['modpass']:
                self.is_mod = True
            else:
                raise ClientError('Invalid password.')

        def get_ip(self):
            return self.transport.get_extra_info('peername')[0]

        def get_hdid(self):
            return self.hdid


        def get_area_hdid(self, area_id):
            info = ''
            try:
                area = self.server.area_manager.get_area_by_id(area_id)
            except AreaError:
                raise
            info += '= Area {}: {} =='.format(area.id, area.name)
            sorted_clients = sorted(area.clients, key=lambda x: x.get_char_name())
            for c in sorted_clients:
                info += '\r\n{}'.format(c.get_char_name())
                if self.is_mod:
                    info += ' ({})'.format(c.get_hdid())
            return info
		
        def get_area_ip(self, area_id):
            info = ''
            try:
                area = self.server.area_manager.get_area_by_id(area_id)
            except AreaError:
                raise
            info += '= Area {}: {} =='.format(area.id, area.name)
            sorted_clients = sorted(area.clients, key=lambda x: x.get_char_name())
            for c in sorted_clients:
                info += '\r\n{}'.format(c.get_char_name())
                if self.is_mod:
                    info += ' ({})'.format(c.get_ip())
            return info
		
        def get_char_name(self):
            if self.char_id == -1:
                return 'CHAR_SELECT'
            return self.server.char_list[self.char_id]

        def change_position(self, pos=''):
            if pos not in ('', 'def', 'pro', 'hld', 'hlp', 'jud', 'wit'):
                raise ClientError('Invalid position. Possible values: def, pro, hld, hlp, jud, wit.')
            self.pos = pos

        def set_mod_call_delay(self):
            self.mod_call_time = round(time.time() * 1000.0 + 30000)

        def can_call_mod(self):
            return (time.time() * 1000.0 - self.mod_call_time) > 0

    def __init__(self, server):
        self.clients = set()
        self.server = server
        self.cur_id = [False] * self.server.config['playerlimit']
        self.clients_list = []

    def new_client(self, transport):
        cur_id = 0
        for i in range(self.server.config['playerlimit']):
                if not self.cur_id[i]:
                    cur_id = i
                    break
        c = self.Client(self.server, transport, cur_id, self.server.get_ipid(transport.get_extra_info('peername')[0]))
        self.clients.add(c)
        self.cur_id[cur_id] = True
        return c

    def remove_client(self, client):
        self.cur_id[client.id] = False
        self.clients.remove(client)
		
    def get_targets(self, client, key, value, local):
        #possible keys: ip, OOC, id, cname, ipid, hdid
        areas = None
        if local:
            areas = [client.area]
        else:
            areas = client.server.area_manager.areas
        targets = []
        for area in areas:
            if key == 'ip':
                for client in area.clients:
                    if value.lower().startswith(client.get_ip().lower()):
                        targets.append(client)
            if key == 'OOC':
                for client in area.clients:
                    if value.lower().startswith(client.name.lower()):
                        targets.append(client)
            if key == 'cname':
                for client in area.clients:
                    if value.lower().startswith(client.get_char_name().lower()):
                        targets.append(client)
            if key == 'id':
                for client in area.clients:
                    if client.id == value:
                        targets.append(client)
            if key == 'ipid':
                for client in area.clients:
                    if client.ipid == value:
                        targets.append(client)
            if key == 'all':
                for key in ['ip', 'OOC', 'id', 'cname', 'ipid', 'hdid']:
                    targets += self.get_targets(client, key, value, local)
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