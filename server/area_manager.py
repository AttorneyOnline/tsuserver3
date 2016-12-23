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
import random

import yaml


class AreaManager:
    class Area:
        def __init__(self, server, name, background, bg_lock):
            self.clients = set()
            self.name = name
            self.background = background
            self.bg_lock = bg_lock
            self.server = server
            self.music_looper = None

        def new_client(self, client):
            self.clients.add(client)

        def remove_client(self, client):
            self.clients.remove(client)

        def is_char_available(self, char_id):
            return char_id not in [x.char_id for x in self.clients]

        def get_rand_avail_char_id(self):
            avail_set = set(range(len(self.server.char_list))) - set([x.char_id for x in self.clients])
            if len(avail_set) == 0:
                raise KeyError('No available characters.')
            return random.choice(tuple(avail_set))

        def send_command(self, cmd, *args):
            for c in self.clients:
                c.send_command(cmd, *args)

        def play_music(self, name, client, length=-1):
            self.send_command('MC', name, client.char_id)
            if length > 0:
                self.music_looper = asyncio.get_event_loop().call_later(length,
                                                                        lambda: self.play_music(name, client, length))
            elif self.music_looper:
                self.music_looper.cancel()

    def __init__(self, server):
        self.server = server
        self.areas = []
        self.load_areas()

    def load_areas(self):
        with open('config/areas.yaml', 'r') as chars:
            areas = yaml.load(chars)
        for area in areas:
            self.areas.append(self.Area(self.server, area, areas[area]['background'], areas[area]['bglock']))

    def default_area(self):
        return self.areas[0]

    def get_area_by_name(self, name):
        for area in self.areas:
            if area.name == name:
                return area
        raise KeyError('Area not found.')
