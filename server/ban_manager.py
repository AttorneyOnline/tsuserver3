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

import json

from server.exceptions import ServerError


class BanManager:
    def __init__(self):
        self.bans = []
        self.load_banlist()

    def load_banlist(self):
        try:
            with open('storage/banlist.json', 'r') as banlist_file:
                self.bans = json.load(banlist_file)
        except FileNotFoundError:
            return

    def write_banlist(self):
        with open('storage/banlist.json', 'w') as banlist_file:
            json.dump(self.bans, banlist_file)

    def add_ban(self, ip, reason):
        if not self.is_banned(ip):
            self.bans.append([ip, reason])
        else:
            raise ServerError('This IPID is already banned.')
        self.write_banlist()

    def remove_ban(self, ip):
        if self.is_banned(ip):
            for ban in bans:
                if ip in ban:
                    self.bans.remove(ban)
        
        else:
            raise ServerError('This IPID is not banned.')
        self.write_banlist()

    def is_banned(self, ipid):
        for ban in self.bans:
            if ip in ban:
                return True
        return False

    def get_ban_reason(self, ipid):
        for ban in self.bans:
            if ip in ban:
                return ban[1]
        raise ServerError('This IPID is not banned.')
