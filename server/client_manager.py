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
        def __init__(self, server, transport, user_id):
            self.transport = transport
            self.hdid = ''
            self.id = user_id
            self.char_id = -1
            self.area = server.area_manager.default_area()
            self.server = server
            self.name = ''
            self.is_mod = False
            self.pos = ''
            self.muted_global = False
            self.muted_adverts = False
            self.is_muted = False
            self.is_ooc_muted = False
            self.pm_mute = False
            self.mod_call_time = 0
            self.in_rp = False

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
            self.send_command('LE', *self.area.get_evidence_list())

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

        def send_limited_area_list(self):
            msg = '=== Areas ==='
            for i, area in enumerate(self.server.area_manager.areas):
                msg += '\r\nArea {}: {}'.format(i, area.name)
                if self.area == area:
                    msg += ' [*]'
            self.send_host_message(msg)

        def get_area_info(self, area_id):
            info = ''
            try:
                area = self.server.area_manager.get_area_by_id(area_id)
            except AreaError:
                raise
            info += '= Area {}: {} =='.format(area.id, area.name)
            sorted_clients = sorted(area.clients, key=lambda x: x.get_char_name())
            for c in sorted_clients:
                info += '\r\n{}'.format(c.get_char_name())
            return info

        def send_area_info(self, area_id):
            try:
                info = self.get_area_info(area_id)
            except AreaError:
                raise
            self.send_host_message(info)

        def send_all_area_info(self):
            info = '== Area List =='
            for i in range(len(self.server.area_manager.areas)):
                #print(len(i.clients))
                if len(self.server.area_manager.areas[i].clients) > 0:
                    info += '\r\n{}'.format(self.get_area_info(i))
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
            self.send_command('LE', *self.area.get_evidence_list())
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
        self.cur_id = 0
        self.server = server

    def new_client(self, transport):
        c = self.Client(self.server, transport, self.cur_id)
        self.clients.add(c)
        self.cur_id += 1
        return c

    def remove_client(self, client):
        self.clients.remove(client)

    def get_targets_by_ip(self, ip):
        clients = []
        for client in self.clients:
            if client.get_ip() == ip:
                clients.append(client)
        return clients
	
    def get_targets_by_hdid(self, hdid):
        clients = []
        for client in self.clients:
            if client.get_hdid() == hdid:
                clients.append(client)
            return clients

    def get_targets_by_hdidip(self, hdid, ip):
        clients = []
        for client in self.clients:
            if client.get_ip() == ip:
                clients.append(client)
            if client.get_hdid() == hdid:
                clients.append(client)
        return clients
		
    def get_targets_by_ooc_name(self, name):
        clients = []
        for client in self.clients:
            if client.name.lower() == name.lower():
                clients.append(client)
        return clients

    def get_targets(self, client, target):
        # check if it's IP but only if mod
        if client.is_mod:
            clients = self.get_targets_by_ip(target)
            if clients:
                return clients
        # check if it's a character name in the same area
        c = client.area.get_target_by_char_name(target)
        if c:
            return [c]
        # check if it's an OOC name
        ooc = self.get_targets_by_ooc_name(target)
        if ooc:
            return ooc
        return None

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