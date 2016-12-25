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
import json


class Banlist:
    def __init__(self):
        self.bans = set()
        self.load_banlist()

    def load_banlist(self):
        try:
            with open('storage/banlist.json', 'r') as banlist_file:
                data = json.loads(banlist_file)
        except FileNotFoundError:
            return
        print(data)  # todo implement

    def write_banlist(self):
        with open('storage/banlist.json', 'w') as banlist_file:
            json.dump(self.bans, banlist_file)

    def add_ban(self, ip):
        self.bans.add(ip)
        self.write_banlist()
