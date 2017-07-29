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

from server.exceptions import ServerError

class ServerpollManager:
    def __init__(self):
        self.vote = []
        self.load_votelist()

    def load_votelist(self):
        try:
            with open('storage/votelist.json', 'r') as votelist_file:
                self.vote = json.load(votelist_file)
        except FileNotFoundError:
            return
        except ValueError:
            return

    def write_votelist(self):
        with open('storage/votelist.json', 'w') as votelist_file:
            json.dump(self.vote, votelist_file)

    def add_votelist(self, ip, hdid):
        if ip not in self.vote:
            self.vote.append(ip)
        if hdid not in self.vote:
            self.vote.append(hdid)
        else:
            raise ServerError('You have already voted.')
        self.write_votelist()


    def has_voted(self, ip, hdid):
        return ip and hdid in self.vote
