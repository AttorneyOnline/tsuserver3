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
from server.exceptions import ClientError, AreaError


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

        def send_raw_message(self, msg):
            print(msg)
            self.transport.write(msg.encode('utf-8'))

        def send_command(self, command, *args):
            if args:
                self.send_raw_message('{}#{}#%'.format(command, '#'.join([str(x) for x in args])))
            else:
                self.send_raw_message('{}#%'.format(command))

        def send_host_message(self, msg):
            self.send_command('CT', self.server.config['hostname'], msg)

        def disconnect(self):
            self.transport.close()

        def change_character(self, char_id):
            if not self.server.is_valid_char_id(char_id):
                raise ClientError('Invalid Character ID.')
            if not self.area.is_char_available(char_id):
                raise ClientError('Character not available.')
            self.char_id = char_id
            self.send_command('PV', self.id, 'CID', self.char_id)

        def change_area(self, area):
            if self.area == area:
                raise ClientError('You are already in this area.')
            if not area.is_char_available(self.char_id):
                try:
                    new_char_id = area.get_rand_avail_char_id()
                except AreaError:
                    raise ClientError('No available characters in that area.')
                self.area.remove_client(self)
                self.area = area
                area.new_client(self)
                self.change_character(new_char_id)
            else:
                self.area.remove_client(self)
                self.area = area
                area.new_client(self)
            self.send_host_message('Changed area to {}.'.format(area.name))

        def send_area_list(self):
            msg = '=== Areas ==='
            for i, area in enumerate(self.server.area_manager.areas):
                msg += '\r\nArea {}: {} (users: {})'.format(i, area.name, len(area.clients))
            self.send_host_message(msg)

        def send_done(self):
            avail_char_ids = set(range(len(self.server.char_list))) - set([x.char_id for x in self.area.clients])
            char_list = [-1] * len(self.server.char_list)
            for x in avail_char_ids:
                char_list[x] = 0
            self.send_command('CharsCheck', *char_list)
            self.send_command('BN', self.area.background)
            self.send_command('MM', 1)
            self.send_command('OPPASS', fantacrypt.fanta_encrypt(self.server.config['guardpass']))
            self.send_command('DONE')

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
