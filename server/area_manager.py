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

import yaml


class AreaManager:
    class Area:
        def __init__(self, name, background, bg_lock):
            self.clients = set()
            self.name = name
            self.background = background
            self.bg_lock = bg_lock

        def new_client(self, client):
            self.clients.add(client)

        def remove_client(self, client):
            self.clients.remove(client)

        def is_char_available(self, char_id):
            return char_id not in [x.char_id for x in self.clients]

        def send_command(self, cmd, *args):
            for c in self.clients:
                c.send_command(cmd, *args)

    def __init__(self):
        self.areas = []
        self.load_areas()

    def load_areas(self):
        with open('config/areas.yaml', 'r') as chars:
            areas = yaml.load(chars)
        for area in areas:
            self.areas.append(self.Area(area, areas[area]['background'], areas[area]['bglock']))

    def default_area(self):
        return self.areas[0]
