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

import asyncio

import yaml

from server.aoprotocol import AOProtocol
from server.area_manager import AreaManager
from server.client_manager import ClientManager
from server.districtclient import DistrictClient
from server.exceptions import ServerError


class TsuServer3:
    def __init__(self):
        self.client_manager = ClientManager(self)
        self.area_manager = AreaManager(self)
        self.version = 'tsuserver3dev'
        self.char_list = None
        self.char_pages_ao1 = None
        self.music_list = None
        self.music_pages_ao1 = None
        self.config = None
        self.load_config()
        self.load_characters()
        self.load_music()
        self.district_client = None

    def start(self):
        loop = asyncio.get_event_loop()

        bound_ip = '0.0.0.0'
        if self.config['local']:
            bound_ip = '127.0.0.1'

        ao_server_crt = loop.create_server(lambda: AOProtocol(self), bound_ip, self.config['port'])
        ao_server = loop.run_until_complete(ao_server_crt)

        if self.config['use_district']:
            self.district_client = DistrictClient(self)
            asyncio.ensure_future(self.district_client.connect(), loop=loop)

        print('Server started.')

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        ao_server.close()
        loop.run_until_complete(ao_server.wait_closed())
        loop.close()

    def new_client(self, transport):
        c = self.client_manager.new_client(transport)
        c.server = self
        c.area = self.area_manager.default_area()
        c.area.new_client(c)
        return c

    def remove_client(self, client):
        client.area.remove_client(client)
        self.client_manager.remove_client(client)

    def get_player_count(self):
        return len(self.client_manager.clients)

    def load_config(self):
        with open('config/config.yaml', 'r') as cfg:
            self.config = yaml.load(cfg)

    def load_characters(self):
        with open('config/characters.yaml', 'r') as chars:
            self.char_list = yaml.load(chars)
        self.build_char_pages_ao1()

    def load_music(self):
        with open('config/music.yaml', 'r') as music:
            self.music_list = yaml.load(music)
        self.build_music_pages_ao1()

    def build_char_pages_ao1(self):
        self.char_pages_ao1 = [self.char_list[x:x + 10] for x in range(0, len(self.char_list), 10)]
        for i in range(len(self.char_list)):
            self.char_pages_ao1[i // 10][i % 10] = '{}#{}&&0&&&0&'.format(i, self.char_list[i])

    def build_music_pages_ao1(self):
        self.music_pages_ao1 = []
        index = 0
        # add areas first
        for area in self.area_manager.areas:
            self.music_pages_ao1.append('{}#{}'.format(index, area.name))
            index += 1
        # then add music
        for category in self.music_list:
            self.music_pages_ao1.append('{}#{}'.format(index, category))
            index += 1
            for song in self.music_list[category]:
                self.music_pages_ao1.append('{}#{}'.format(index, song['name']))
                index += 1
        self.music_pages_ao1 = [self.music_pages_ao1[x:x + 10] for x in range(0, len(self.music_pages_ao1), 10)]

    def is_valid_char_id(self, char_id):
        return len(self.char_list) > char_id >= 0

    def get_char_id_by_name(self, name):
        for i, ch in enumerate(self.char_list):
            if ch == name:
                return i
        raise ServerError('Character not found.')

    def get_char_name_by_id(self, char_id):
        try:
            return self.char_list[char_id]
        except IndexError:
            raise ServerError('Invalid character ID.')

    def get_song_data(self, music):
        for category in self.music_list:
            if category == music:
                return category, -1
            for song in self.music_list[category]:
                if song['name'] == music:
                    return song['name'], song['length']
        raise ServerError('Music not found.')

    def broadcast_global(self, client, msg):
        for area in self.area_manager.areas:
            area.send_command('CT', '{}[{}][{}]'.format(self.config['hostname'], client.area.id,
                                                        self.get_char_name_by_id(client.char_id)), msg)
        if self.config['use_district']:
            self.district_client.send_raw_message('TEST')
